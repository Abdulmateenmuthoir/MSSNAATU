from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import ROLE_MEMBER, Student
from apps.blog.models import Post
from apps.events.models import Event, Registration
from apps.finance.models import DuesCycle, Payment
from apps.library.models import PastQuestion

from .forms import ContactForm
from .models import Announcement, Committee, Executive, Faculty


def home(request):
    now = timezone.now()
    upcoming_events = (
        Event.objects.filter(is_published=True, starts_at__gte=now).order_by("starts_at")[:3]
    )
    latest_posts = Post.objects.filter(is_published=True, published_at__lte=now)[:3]
    current_executives = Executive.objects.filter(session="1448/1449 AH")[:6]
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
    people = Executive.objects.filter(session=selected)
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
