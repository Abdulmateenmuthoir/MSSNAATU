import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.emails import send_donation_receipt, send_dues_reminder, send_payment_receipt
from apps.accounts.models import ROLE_FINANCE, ROLE_MEMBER, Student
from apps.core.models import LEVEL_CHOICES

from .forms import DuesCycleForm, DuesPaymentForm
from .models import Donation, DuesCycle, Payment, ReminderLog
from .services import initialize_donation, initialize_transaction, is_configured, verify_transaction


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
    payment_data = request.POST.copy()
    if payment_data.get("custom_amount", "").strip():
        payment_data["amount"] = payment_data["custom_amount"]
    form = DuesPaymentForm(payment_data, minimum=cycle.amount)
    if form.is_valid():
        amount = form.cleaned_data["amount"]
    elif pending and not request.POST.get("amount") and not request.POST.get("custom_amount", "").strip():
        amount = pending.amount
    else:
        messages.error(request, form.errors.get("amount", ["Enter a valid payment amount."])[0])
        return redirect("finance:dues")

    payment = pending if pending and pending.amount == amount else None
    payment = payment or Payment.objects.create(student=request.user, cycle=cycle, amount=amount)
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
        expected_kobo = int(payment.amount * 100)
        if payload.get("amount") != expected_kobo or payload.get("currency") != "NGN":
            payment.status = Payment.FAILED
            payment.save(update_fields=["status"])
            messages.error(request, "The confirmed Paystack amount did not match this payment. Contact the Finance Officer.")
            return redirect("finance:dues")
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


def donate(request):
    return render(request, "finance/donate.html", {"paystack_ready": is_configured()})


@require_POST
def initialize_donation_view(request):
    from decimal import Decimal, InvalidOperation

    try:
        amount = Decimal(request.POST.get("custom_amount") or request.POST.get("preset", ""))
    except (InvalidOperation, TypeError):
        messages.error(request, "Enter a valid donation amount.")
        return redirect("donate")
    if amount < Decimal("100") or amount > Decimal("10000000"):
        messages.error(request, "Donations must be at least ₦100 and no more than ₦10,000,000.")
        return redirect("donate")
    email = request.POST.get("email", "").strip()
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Enter a valid email address for your receipt.")
        return redirect("donate")
    donor_name = request.POST.get("donor_name", "").strip()[:160]
    allowed_causes = {"General Society Support", "Da'wah and Programmes", "Student Welfare", "Academic Support"}
    cause = request.POST.get("cause", "General Society Support")
    if cause not in allowed_causes:
        cause = "General Society Support"
    if not is_configured():
        messages.error(request, "Online donations are temporarily unavailable. Please check back soon.")
        return redirect("donate")
    donation = Donation.objects.create(donor_name=donor_name, email=email, cause=cause, amount=amount)
    url, error = initialize_donation(donation)
    if url:
        return redirect(url)
    donation.status = Donation.FAILED
    donation.save(update_fields=["status"])
    messages.error(request, error or "The payment gateway is unavailable right now.")
    return redirect("donate")


def donation_callback(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")
    if not reference:
        messages.error(request, "The donation reference was missing.")
        return redirect("donate")
    donation = Donation.objects.filter(reference=reference).first()
    if not donation:
        messages.error(request, "We could not find that donation.")
        return redirect("donate")
    if donation.status != Donation.SUCCESS:
        success, payload = verify_transaction(reference)
        if success and payload.get("amount") == int(donation.amount * 100) and payload.get("currency") == "NGN":
            donation.status = Donation.SUCCESS
            donation.gateway_reference = payload.get("reference", reference)
            donation.paid_at = timezone.now()
            donation.receipt_sent = send_donation_receipt(donation)
            donation.save(update_fields=["status", "gateway_reference", "paid_at", "receipt_sent"])
            messages.success(request, "Your donation has been confirmed. Thank you for supporting MSSN AATU.")
        else:
            donation.status = Donation.FAILED
            donation.save(update_fields=["status"])
            messages.error(request, "We could not confirm this donation. Please contact the Public Relations Officer if you were charged.")
    return redirect("donation_result", reference=donation.reference)


def donation_result(request, reference):
    donation = get_object_or_404(Donation, reference=reference)
    return render(request, "finance/donation_result.html", {"donation": donation})


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
