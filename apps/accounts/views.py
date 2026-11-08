import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from apps.core.models import LEVEL_CHOICES
from apps.finance.models import DuesCycle, Payment

from .decorators import role_required
from .emails import send_credentials, send_password_reset
from .forms import (
    CSVImportForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    LoginForm,
    ProfileForm,
    PromoteForm,
    SetPasswordForm,
    StudentForm,
)
from .importers import import_students
from .models import ROLE_CHOICES, Student, generate_temp_password

logger = logging.getLogger(__name__)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        auth_login(request, user)
        request.session.pop("password_prompt_dismissed", None)
        user.last_seen = timezone.now()
        user.save(update_fields=["last_seen"])
        if not form.cleaned_data.get("remember_me"):
            request.session.set_expiry(0)
        if user.must_change_password:
            return redirect("accounts:password_setup")
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("dashboard:home")
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("core:home")


@login_required
def password_setup(request):
    user = request.user
    if not user.must_change_password:
        return redirect("dashboard:home")
    form = SetPasswordForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, user)
        user.password_set_at = timezone.now()
        user.save(update_fields=["password_set_at"])
        request.session.pop("password_prompt_dismissed", None)
        messages.success(request, "Your new password is set. Welcome to your dashboard.")
        return redirect("dashboard:home")
    return render(request, "accounts/password_setup.html", {"form": form})


@login_required
def password_setup_skip(request):
    if request.method != "POST":
        return redirect("accounts:password_setup")
    request.session["password_prompt_dismissed"] = True
    messages.info(request, "You are using your temporary password. Change it from your profile whenever you're ready.")
    return redirect("dashboard:home")


@login_required
def password_change(request):
    form = ChangePasswordForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        student.password_set_at = timezone.now()
        student.save(update_fields=["password_set_at"])
        update_session_auth_hash(request, student)
        request.session.pop("password_prompt_dismissed", None)
        messages.success(request, "Your password has been changed.")
        return redirect("accounts:profile")
    return render(request, "accounts/password_change.html", {"form": form})


def password_forgot(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["identifier"].strip()
        student = Student.objects.filter(
            Q(matric_no__iexact=identifier) | Q(email__iexact=identifier)
        ).first()
        if student and student.is_active:
            uid = urlsafe_base64_encode(force_bytes(student.pk))
            token = default_token_generator.make_token(student)
            reset_path = reverse("accounts:password_reset", args=[uid, token])
            send_password_reset(student, request.build_absolute_uri(reset_path))
        return redirect("accounts:password_forgot_done")
    return render(request, "accounts/password_forgot.html", {"form": form})


def password_forgot_done(request):
    return render(request, "accounts/password_forgot_done.html")


def password_reset(request, uidb64, token):
    student = None
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        student = Student.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, Student.DoesNotExist):
        student = None

    valid_link = student is not None and default_token_generator.check_token(student, token)
    if not valid_link:
        return render(request, "accounts/password_reset_confirm.html", {"validlink": False}, status=400)

    form = SetPasswordForm(request.POST or None, user=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        student.password_set_at = timezone.now()
        student.save(update_fields=["password_set_at"])
        messages.success(request, "Your password has been reset. You can now sign in.")
        return redirect("accounts:password_reset_complete")
    return render(
        request,
        "accounts/password_reset_confirm.html",
        {"validlink": True, "form": form, "student": student},
    )


def password_reset_complete(request):
    return render(request, "accounts/password_reset_complete.html")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    stats = {
        "registrations": request.user.event_registrations.count(),
        "comments": request.user.comments.count(),
        "payments": request.user.payments.filter(status=Payment.SUCCESS).count(),
    }
    return render(request, "accounts/profile.html", {"form": form, "stats": stats})


# ---------------------------------------------------------------------------
# Student administration
# ---------------------------------------------------------------------------


@role_required()
def student_list(request):
    students = Student.objects.select_related("faculty", "department")
    query = (request.GET.get("q") or "").strip()
    role = request.GET.get("role", "")
    level = request.GET.get("level", "")
    if query:
        students = students.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(matric_no__icontains=query)
            | Q(email__icontains=query)
        )
    if role:
        students = students.filter(role=role)
    if level:
        students = students.filter(level=level)
    paginator = Paginator(students, 20)
    page = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "dashboard/students/list.html",
        {
            "page": page,
            "query": query,
            "role": role,
            "level": level,
            "query_string": query_params.urlencode(),
            "total": students.count(),
            "role_choices": ROLE_CHOICES,
            "levels": LEVEL_CHOICES,
        },
    )


@role_required()
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save(commit=False)
        password = generate_temp_password()
        student.set_password(password)
        student.must_change_password = True
        student.save()
        emailed = send_credentials(student, password)
        request.session["temp_credentials"] = {
            "name": student.full_name,
            "matric_no": student.matric_no,
            "email": student.email,
            "password": password,
            "email_sent": emailed,
        }
        messages.success(request, f"{student.full_name} has been added.")
        return redirect("people:credentials")
    return render(request, "dashboard/students/form.html", {"form": form, "student": None})


@role_required()
def student_credentials(request):
    credentials = request.session.pop("temp_credentials", None)
    if not credentials:
        messages.info(request, "No new login details to show.")
        return redirect("people:list")
    return render(request, "dashboard/students/credentials.html", {"credentials": credentials})


@role_required()
def student_detail(request, pk):
    student = get_object_or_404(
        Student.objects.select_related("faculty", "department"), pk=pk
    )
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student record updated.")
        return redirect("people:detail", pk=student.pk)
    registrations = student.event_registrations.select_related("event")[:5]
    payments = student.payments.select_related("cycle")[:5]
    return render(
        request,
        "dashboard/students/detail.html",
        {"form": form, "student": student, "registrations": registrations, "payments": payments},
    )


@role_required()
def student_import(request):
    form = CSVImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            created, errors = import_students(
                form.cleaned_data["csv_file"],
                send_emails=form.cleaned_data["send_emails"],
            )
        except Exception as exc:
            logger.exception("Student import failed")
            messages.error(request, f"The file could not be processed: {exc}")
        else:
            request.session["import_result"] = {
                "created": created,
                "errors": errors,
                "emailed": form.cleaned_data["send_emails"],
            }
            return redirect("people:import_result")
    return render(request, "dashboard/students/import.html", {"form": form})


@role_required()
def student_import_result(request):
    result = request.session.pop("import_result", None)
    if result is None:
        return redirect("people:import")
    return render(request, "dashboard/students/import_result.html", result)


@role_required()
@require_POST
def student_resend_credentials(request, pk):
    student = get_object_or_404(Student, pk=pk)
    password = generate_temp_password()
    student.set_password(password)
    student.must_change_password = True
    student.save(update_fields=["password", "must_change_password"])
    emailed = send_credentials(student, password)
    request.session["temp_credentials"] = {
        "name": student.full_name,
        "matric_no": student.matric_no,
        "email": student.email,
        "password": password,
        "email_sent": emailed,
    }
    messages.success(request, "New login details generated.")
    return redirect("people:credentials")


@role_required()
@require_POST
def student_toggle_active(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if student.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        student.is_active = not student.is_active
        student.save(update_fields=["is_active"])
        messages.success(request, f"{student.full_name} is now {'active' if student.is_active else 'inactive'}.")
    return redirect("people:detail", pk=student.pk)


@role_required()
def promote_levels(request):
    form = PromoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        promotions = {"100": "200", "200": "300", "300": "400", "400": "500", "500": "600", "600": "700"}
        changed = 0
        for old, new in promotions.items():
            changed += Student.objects.filter(level=old).update(level=new)
        messages.success(request, f"{changed} student record(s) promoted to the next level.")
        return redirect("people:list")
    counts = (
        Student.objects.exclude(level="")
        .values("level")
        .annotate(total=Count("id"))
        .order_by("level")
    )
    return render(request, "dashboard/students/promote.html", {"form": form, "counts": counts})
