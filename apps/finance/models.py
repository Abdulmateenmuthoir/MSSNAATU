import uuid
from decimal import Decimal

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible


def generate_reference():
    return f"MSSN-{uuid.uuid4().hex[:12].upper()}"


@deconstructible
class PrivateReceiptStorage(FileSystemStorage):
    """Store receipts outside MEDIA_ROOT; access them only through the finance view."""

    def __init__(self):
        super().__init__(location=settings.BASE_DIR / "private_uploads")


class DuesCycle(models.Model):
    session = models.CharField(max_length=40, unique=True, help_text="e.g. 1448/1449 AH")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2000.00"))
    due_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session} — ₦{self.amount:,.0f}"

    @property
    def paid_count(self):
        return self.payments.filter(status=Payment.SUCCESS).values("student").distinct().count()

    @property
    def collected_total(self):
        return self.payments.filter(status=Payment.SUCCESS).aggregate(total=models.Sum("amount"))["total"] or 0


class Payment(models.Model):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    STATUS_CHOICES = [(PENDING, "Pending"), (SUCCESS, "Paid"), (FAILED, "Failed")]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    cycle = models.ForeignKey(DuesCycle, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=80, unique=True, default=generate_reference, editable=False)
    gateway = models.CharField(max_length=30, default="paystack")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    gateway_reference = models.CharField(max_length=120, blank=True)
    receipt = models.FileField(
        upload_to="dues-receipts/%Y/%m/",
        storage=PrivateReceiptStorage(),
        blank=True,
    )
    review_note = models.CharField(max_length=300, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reviewed_dues_payments",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.matric_no} — {self.get_status_display()}"

    def mark_paid(self, gateway_reference=""):
        self.status = self.SUCCESS
        self.paid_at = timezone.now()
        if gateway_reference:
            self.gateway_reference = gateway_reference
        self.save(update_fields=["status", "paid_at", "gateway_reference"])

    @property
    def receipt_number(self):
        token = str(self.reference).removeprefix("MSSN-")[:8].upper()
        return f"MSSN-{self.created_at:%Y%m}-{token}"

    @property
    def amount_display(self):
        return f"₦{self.amount:,.0f}"


class ReminderLog(models.Model):
    cycle = models.ForeignKey(DuesCycle, on_delete=models.CASCADE, related_name="reminders")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dues_reminders")
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Reminder → {self.student.matric_no}"
