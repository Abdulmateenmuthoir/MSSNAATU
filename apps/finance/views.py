import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.emails import send_dues_reminder, send_payment_receipt
from apps.accounts.models import ROLE_FINANCE, ROLE_MEMBER, Student
from apps.core.models import LEVEL_CHOICES

from .forms import DuesCycleForm
from .models import DuesCycle, Payment, ReminderLog
from .services import initialize_transaction, is_configured, verify_transaction


def _payments_for(cycle):
    return Payment.objects.filter(cycle=cycle, status=Payment.SUCCESS)


def _paid_student_ids(cycle):
    return _payments_for(cycle).values_list("student_id", flat=True)


def _unpaid_students(cycle):
    return Student.objects.filter(is_active=True, role=ROLE_MEMBER).exclude(id__in=_paid_student_ids(cycle))


@login_required
def dues_home(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    payment = None
    pending_payment = None
    history = []
    if cycle:
        payment = (
            request.user.payments.filter(cycle=cycle, status=Payment.SUCCESS).order_by("-paid_at").first()
        )
        pending_payment = request.user.payments.filter(
            cycle=cycle, gateway="paystack", status=Payment.PENDING
        ).order_by("-created_at").first()
        history = request.user.payments.select_related("cycle").order_by("-created_at")
    return render(
        request,
        "finance/dues.html",
        {
            "cycle": cycle,
            "payment": payment,
            "pending_payment": pending_payment,
            "history": history,
            "paystack_ready": is_configured(),
        },
    )


@login_required
@require_POST
def initialize_payment(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    if not cycle:
        messages.error(request, "No active dues cycle has been set yet.")
        return redirect("finance:dues")
    if request.user.payments.filter(cycle=cycle, status=Payment.SUCCESS).exists():
        messages.info(request, "Your dues for this session are already paid.")
        return redirect("finance:dues")

    if not is_configured():
        messages.error(request, "Paystack is not configured yet. Please check back after the Finance Officer enables online payment.")
        return redirect("finance:dues")
    pending = request.user.payments.filter(cycle=cycle, status=Payment.PENDING, gateway="paystack").order_by("-created_at").first()
    payment = pending or Payment.objects.create(student=request.user, cycle=cycle, amount=cycle.amount)
    url, error = initialize_transaction(payment)
    if url:
        return redirect(url)
    messages.error(request, error or "The payment gateway is unavailable right now.")
    return redirect("finance:dues")


def callback(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")
    if not reference:
        messages.error(request, "The payment reference was missing.")
        return redirect("finance:dues")
    payment = Payment.objects.filter(reference=reference).select_related("student", "cycle").first()
    if not payment:
        messages.error(request, "We could not find that payment.")
        return redirect("finance:dues")

    if payment.status == Payment.SUCCESS:
        messages.info(request, "This payment has already been confirmed.")
        return redirect("finance:receipt", reference=payment.reference)

    success, payload = verify_transaction(reference)
    if success:
        payment.mark_paid(payload.get("reference", reference))
        send_payment_receipt(payment)
        messages.success(request, "Payment confirmed. Jazakumullahu khairan.")
        if request.user.is_authenticated and request.user == payment.student:
            return redirect("finance:receipt", reference=payment.reference)
        return redirect("finance:dues")
    payment.status = Payment.FAILED
    payment.save(update_fields=["status"])
    messages.error(request, f"Payment was not confirmed: {payload}")
    return redirect("finance:dues")


@login_required
def receipt(request, reference):
    payment = get_object_or_404(Payment.objects.select_related("student", "cycle"), reference=reference)
    if payment.student_id != request.user.id and not request.user.can_manage_finance:
        messages.error(request, "You do not have access to that receipt.")
        return redirect("finance:dues")
    return render(request, "finance/receipt.html", {"payment": payment})


# ---------------------------------------------------------------------------
# Finance dashboard
# ---------------------------------------------------------------------------


@role_required(ROLE_FINANCE)
def finance_dashboard(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    stats = {}
    outstanding = Student.objects.none()
    recent = Payment.objects.none()
    if cycle:
        paid_payments = _payments_for(cycle)
        member_count = Student.objects.filter(is_active=True).count()
        paid_count = paid_payments.values("student").distinct().count()
        collected = paid_payments.aggregate(total=Sum("amount"))["total"] or 0
        outstanding = _unpaid_students(cycle).select_related("faculty", "department")
        recent = paid_payments.select_related("student").order_by("-paid_at")[:8]
        stats = {
            "member_count": member_count,
            "paid_count": paid_count,
            "unpaid_count": member_count - paid_count,
            "collected": collected,
            "expected": member_count * cycle.amount,
            "rate": round((paid_count / member_count) * 100) if member_count else 0,
        }
    level = request.GET.get("level", "")
    if level and cycle:
        outstanding = outstanding.filter(level=level)
    return render(
        request,
        "dashboard/finance/overview.html",
        {
            "cycle": cycle,
            "stats": stats,
            "outstanding": outstanding[:12],
            "outstanding_total": outstanding.count() if cycle else 0,
            "recent": recent,
            "levels": LEVEL_CHOICES,
            "level": level,
            "form": DuesCycleForm(instance=cycle) if cycle else DuesCycleForm(),
        },
    )


@role_required(ROLE_FINANCE)
@require_POST
def save_cycle(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    form = DuesCycleForm(request.POST, instance=cycle)
    if form.is_valid():
        form.save()
        messages.success(request, "Dues cycle saved.")
    else:
        messages.error(request, "The dues cycle could not be saved. Check the amount and date.")
    return redirect("money:overview")


@role_required(ROLE_FINANCE)
def export_payments(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="mssnaatu-dues.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student", "Matric number", "Email", "Level", "Department", "Amount", "Status", "Reference", "Paid at"])
    payments = Payment.objects.select_related("student", "student__department")
    if cycle:
        payments = payments.filter(cycle=cycle)
    for payment in payments:
        student = payment.student
        writer.writerow(
            [
                student.full_name,
                student.matric_no,
                student.email,
                student.get_level_display(),
                student.department.name if student.department else "",
                payment.amount,
                payment.get_status_display(),
                payment.reference,
                payment.paid_at.strftime("%Y-%m-%d %H:%M") if payment.paid_at else "",
            ]
        )
    return response


@role_required(ROLE_FINANCE)
@require_POST
def send_reminders(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    if not cycle:
        messages.error(request, "Set an active dues cycle first.")
        return redirect("money:overview")
    targets = _unpaid_students(cycle)
    sent = 0
    for student in targets:
        pay_url = f"{settings.SITE_URL}{reverse('finance:dues')}"
        if send_dues_reminder(student, cycle, pay_url):
            ReminderLog.objects.create(cycle=cycle, student=student)
            sent += 1
    messages.success(request, f"Dues reminder sent to {sent} unpaid member(s).")
    return redirect("money:overview")


@role_required(ROLE_FINANCE)
def payments_list(request):
    cycle = DuesCycle.objects.filter(is_active=True).first()
    payments = Payment.objects.select_related("student", "cycle").order_by("-created_at")
    if cycle:
        payments = payments.filter(cycle=cycle)
    status = request.GET.get("status", "")
    if status:
        payments = payments.filter(status=status)
    return render(
        request,
        "dashboard/finance/payments.html",
        {"payments": payments, "cycle": cycle, "status": status},
    )
