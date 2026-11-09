import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.emails import send_event_confirmation, send_event_reminder
from apps.accounts.models import ROLE_EVENTS
from apps.core.models import Department, LEVEL_CHOICES

from .forms import EventForm, ProgramForm
from .models import Event, Program, Registration


def event_list(request):
    now = timezone.now()
    show = request.GET.get("show", "upcoming")
    query = (request.GET.get("q") or "").strip()
    events = Event.objects.filter(is_published=True).annotate(reg_count=Count("registrations"))
    if show == "past":
        events = events.filter(starts_at__lt=now).order_by("-starts_at")
    else:
        show = "upcoming"
        events = events.filter(starts_at__gte=now).order_by("starts_at")
    if query:
        events = events.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(venue__icontains=query))
    paginator = Paginator(events, 9)
    page = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "events/list.html",
        {
            "page": page,
            "show": show,
            "query": query,
            "query_string": query_params.urlencode(),
            "featured": page.object_list[0] if page.object_list else None,
        },
    )


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related("created_by"), slug=slug)
    if not event.is_published:
        raise Http404
    registration = None
    if request.user.is_authenticated:
        registration = Registration.objects.filter(event=event, student=request.user).first()
    context = {
        "event": event,
        "registration": registration,
        "eligible": event.eligible_for(request.user) if request.user.is_authenticated else True,
        "registration_count": event.registrations.count(),
    }
    return render(request, "events/detail.html", context)


def programme_list(request):
    return render(request, "events/programmes.html", {"programmes": Program.objects.filter(is_active=True)})


@login_required
@require_POST
def register(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)
    if Registration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "You are already registered for this programme.")
        return redirect(event.get_absolute_url())
    if not event.eligible_for(request.user):
        messages.error(request, f"This programme is for {event.get_eligibility_display().lower()}.")
        return redirect(event.get_absolute_url())
    if not event.registration_open:
        messages.error(request, "Registration for this programme is closed.")
        return redirect(event.get_absolute_url())
    registration, created = Registration.objects.get_or_create(event=event, student=request.user)
    if created:
        send_event_confirmation(registration)
        messages.success(request, f"You're registered for {event.title}. A confirmation email is on its way.")
    else:
        messages.info(request, "You are already registered for this programme.")
    return redirect(event.get_absolute_url())


@login_required
@require_POST
def cancel_registration(request, slug):
    event = get_object_or_404(Event, slug=slug)
    deleted, _ = Registration.objects.filter(event=event, student=request.user).delete()
    if deleted:
        messages.success(request, "Your registration has been cancelled.")
    return redirect(event.get_absolute_url())


# ---------------------------------------------------------------------------
# Events dashboard
# ---------------------------------------------------------------------------


@role_required(ROLE_EVENTS)
def manage_list(request):
    events = Event.objects.annotate(reg_count=Count("registrations")).select_related("created_by")
    return render(request, "dashboard/events/list.html", {"events": events})


@role_required(ROLE_EVENTS)
def event_create(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, "Event created.")
        return redirect("eventmanager:list")
    return render(request, "dashboard/events/form.html", {"form": form, "event": None})


@role_required(ROLE_EVENTS)
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect("eventmanager:list")
    return render(request, "dashboard/events/form.html", {"form": form, "event": event})


@role_required(ROLE_EVENTS)
@require_POST
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    title = event.title
    event.delete()
    messages.success(request, f"“{title}” was deleted.")
    return redirect("eventmanager:list")


@role_required(ROLE_EVENTS)
def registrations(request, pk):
    event = get_object_or_404(Event, pk=pk)
    rows = event.registrations.select_related("student__faculty", "student__department")
    level = request.GET.get("level", "")
    department = request.GET.get("department", "")
    if level:
        rows = rows.filter(student__level=level)
    if department:
        rows = rows.filter(student__department_id=department)
    return render(
        request,
        "dashboard/events/registrations.html",
        {
            "event": event,
            "registrations": rows,
            "level": level,
            "department": department,
            "levels": LEVEL_CHOICES,
            "departments": Department.objects.all(),
        },
    )


@role_required(ROLE_EVENTS)
def registrations_export(request, pk):
    event = get_object_or_404(Event, pk=pk)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{event.slug}-registrations.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Matric number", "Email", "Gender", "Level", "Department", "Faculty", "Registered at"])
    for registration in event.registrations.select_related("student__department", "student__faculty"):
        student = registration.student
        writer.writerow(
            [
                student.full_name,
                student.matric_no,
                student.email,
                student.get_gender_display(),
                student.get_level_display(),
                student.department.name if student.department else "",
                student.faculty.name if student.faculty else "",
                registration.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )
    return response


@role_required(ROLE_EVENTS)
@require_POST
def send_reminders(request, pk):
    event = get_object_or_404(Event, pk=pk)
    sent = 0
    for registration in event.registrations.select_related("student"):
        if send_event_reminder(event, registration.student):
            sent += 1
    messages.success(request, f"Reminder sent to {sent} registrant(s).")
    return redirect("eventmanager:registrations", pk=event.pk)


# ---------------------------------------------------------------------------
# Recurring society programmes (distinct from dated events)
# ---------------------------------------------------------------------------


@role_required(ROLE_EVENTS)
def program_manage_list(request):
    return render(request, "dashboard/programmes/list.html", {"programmes": Program.objects.all()})


@role_required(ROLE_EVENTS)
def program_create(request):
    form = ProgramForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Society programme added.")
        return redirect("programmeadmin:list")
    return render(request, "dashboard/programmes/form.html", {"form": form, "programme": None})


@role_required(ROLE_EVENTS)
def program_edit(request, pk):
    programme = get_object_or_404(Program, pk=pk)
    form = ProgramForm(request.POST or None, instance=programme)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Society programme updated.")
        return redirect("programmeadmin:list")
    return render(request, "dashboard/programmes/form.html", {"form": form, "programme": programme})


@role_required(ROLE_EVENTS)
@require_POST
def program_delete(request, pk):
    programme = get_object_or_404(Program, pk=pk)
    name = programme.name
    programme.delete()
    messages.success(request, f"{name} was removed.")
    return redirect("programmeadmin:list")
