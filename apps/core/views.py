from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from mimetypes import guess_type
from pathlib import Path

from apps.accounts.models import ROLE_MEMBER, Student
from apps.blog.models import Post
from apps.events.models import Event, Registration
from apps.finance.models import DuesCycle, Payment
from apps.library.models import PastQuestion

from .forms import ContactForm, NewsletterForm
from .models import Announcement, Committee, Executive, Faculty, NewsletterSubscriber


def public_media(request, path):
    """Serve only image uploads used on public pages (never library documents)."""
    allowed_directories = {"avatars", "news", "events", "executives"}
    allowed_extensions = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
    parts = Path(path).parts
    if len(parts) < 2 or parts[0] not in allowed_directories:
        raise Http404

    image_path = Path(settings.MEDIA_ROOT, path).resolve()
    media_root = Path(settings.MEDIA_ROOT).resolve()
    try:
        image_path.relative_to(media_root)
    except ValueError:
        raise Http404
    if image_path.suffix.lower() not in allowed_extensions or not image_path.is_file():
        raise Http404

    response = FileResponse(
        image_path.open("rb"),
        content_type=guess_type(image_path.name)[0] or "application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "public, max-age=86400"
    return response


def home(request):
    now = timezone.now()
    upcoming_events = (
        Event.objects.filter(is_published=True, starts_at__gte=now).order_by("starts_at")[:3]
    )
    latest_posts = Post.objects.filter(is_published=True, published_at__lte=now)[:3]
    current_executives = Executive.objects.filter(is_current=True).select_related("department")[:6]
    stats = {
        "members": Student.objects.filter(is_active=True).count(),
        "events": Event.objects.filter(is_published=True).count(),
        "questions": PastQuestion.objects.count(),
        "faculties": Faculty.objects.count(),
    }
    return render(
        request,
        "core/home.html",
        {
            "upcoming_events": upcoming_events,
            "latest_posts": latest_posts,
            "current_executives": current_executives,
            "stats": stats,
        },
    )


def about(request):
    stats = {
        "members": Student.objects.filter(is_active=True).count(),
        "faculties": Faculty.objects.count(),
        "questions": PastQuestion.objects.count(),
    }
    return render(request, "core/about.html", {"stats": stats})


def executives(request):
    sessions = list(
        Executive.objects.values_list("session", flat=True).distinct().order_by("-session")
    )
    selected = request.GET.get("session") or (sessions[0] if sessions else "1448/1449 AH")
    people = Executive.objects.filter(session=selected).select_related("department")
    return render(
        request,
        "core/executives.html",
        {"sessions": sessions, "selected_session": selected, "executives": people},
    )


def branches(request):
    return render(request, "core/branches.html", {
        "health_courses": ["Medical Laboratory Science", "Nursing Science", "Public Health"],
        "engineering_courses": [
            "Agricultural Engineering", "Biomedical Engineering", "Chemical Engineering", "Civil Engineering",
            "Computer Engineering", "Electrical and Electronic Engineering", "Food Science and Technology",
            "Industrial and Production Engineering", "Mechanical Engineering", "Mechatronics Engineering", "Petroleum Engineering",
        ],
        "science_courses": [
            "Biochemistry", "Biotechnology", "Computer Science", "Cyber Security", "Forensic Science",
            "Industrial Chemistry", "Mathematics", "Microbiology", "Physics with Electronics",
            "Science Laboratory Technology", "Software Engineering", "Statistics",
        ],
        "environmental_courses": [
            "Architecture", "Building Technology", "Estate Management", "Quantity Surveying",
            "Surveying and Geoinformatics", "Urban and Regional Planning",
        ],
    })
    selected = request.GET.get("session") or (sessions[0] if sessions else "1448/1449 AH")
    people = Executive.objects.filter(session=selected).select_related("department")
    return render(
        request,
        "core/executives.html",
        {"sessions": sessions, "selected_session": selected, "executives": people},
    )


def committees(request):
    sessions = list(
        Committee.objects.values_list("session", flat=True).distinct().order_by("-session")
    )
    selected = request.GET.get("session") or (sessions[0] if sessions else "1448/1449 AH")
    groups = Committee.objects.filter(session=selected).prefetch_related("members")
    return render(
        request,
        "core/committees.html",
        {"sessions": sessions, "selected_session": selected, "committees": groups},
    )


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your message has reached the PRO office. We will get back to you shortly.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def newsletter_subscribe(request):
    if request.method != "POST":
        return redirect("core:home")
    form = NewsletterForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please enter a valid email address to subscribe.")
        return redirect(f"{reverse('core:home')}#newsletter")

    email = form.cleaned_data["email"].strip().lower()
    name = form.cleaned_data["name"].strip()
    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={"name": name, "is_active": True},
    )
    if not created and not subscriber.is_active:
        subscriber.is_active = True
        if name:
            subscriber.name = name
        subscriber.save(update_fields=["name", "is_active"])
    messages.success(request, "You’re subscribed to useful MSSN AATU updates.")
    return redirect(f"{reverse('core:home')}#newsletter")


@login_required
def dashboard(request):
    user = request.user
    now = timezone.now()
    active_cycle = DuesCycle.objects.filter(is_active=True).first()
    my_payment = None
    if active_cycle:
        my_payment = (
            user.payments.filter(cycle=active_cycle, status=Payment.SUCCESS).order_by("-paid_at").first()
        )

    next_event = Event.objects.filter(is_published=True, starts_at__gte=now).order_by("starts_at").first()
    my_registration = None
    if next_event:
        my_registration = Registration.objects.filter(event=next_event, student=user).first()

    announcements = Announcement.objects.filter(is_active=True)[:2]
    latest_posts = Post.objects.filter(is_published=True)[:3]
    my_registrations = user.event_registrations.select_related("event").order_by("-created_at")[:4]

    context = {
        "active_cycle": active_cycle,
        "my_payment": my_payment,
        "next_event": next_event,
        "my_registration": my_registration,
        "announcements": announcements,
        "latest_posts": latest_posts,
        "my_registrations": my_registrations,
        "my_registration_count": user.event_registrations.count(),
        "is_admin": user.is_administrator,
        "question_count": PastQuestion.objects.count(),
        "post_count": Post.objects.filter(is_published=True).count(),
    }

    if user.is_administrator or user.role != ROLE_MEMBER:
        context.update(
            {
                "member_count": Student.objects.filter(is_active=True).count(),
                "paid_count": active_cycle.paid_count if active_cycle else 0,
                "unpaid_count": Student.objects.filter(is_active=True, payments__isnull=True).count()
                if active_cycle
                else 0,
                "event_count": Event.objects.filter(starts_at__gte=now, is_published=True).count(),
                "post_count": Post.objects.filter(is_published=True).count(),
                "question_count": PastQuestion.objects.count(),
                "recent_registrations": Registration.objects.select_related("student", "event")[:5],
                "recent_payments": Payment.objects.filter(status=Payment.SUCCESS).select_related("student", "cycle")[:5]
                if user.can_manage_finance
                else [],
            }
        )
    return render(request, "dashboard/overview.html", context)


def health(request):
    return JsonResponse({"status": "ok", "service": "mssnaatu"})


def error_403(request, exception):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
