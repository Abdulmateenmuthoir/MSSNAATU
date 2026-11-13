from django.contrib import admin

from .models import Donation, DuesCycle, Payment, ReminderLog


@admin.register(DuesCycle)
class DuesCycleAdmin(admin.ModelAdmin):
    list_display = ("session", "amount", "due_date", "is_active", "paid_count", "collected_total")
    list_filter = ("is_active",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "cycle", "amount", "status", "gateway", "paid_at")
    list_filter = ("status", "gateway", "cycle")
    search_fields = ("student__first_name", "student__last_name", "student__matric_no", "reference")
    readonly_fields = ("reference", "created_at", "paid_at")


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("student", "cycle", "sent_at", "success")
    list_filter = ("success", "cycle")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donor_name", "email", "cause", "amount", "status", "paid_at")
    list_filter = ("status", "cause")
    search_fields = ("donor_name", "email", "reference", "gateway_reference")
    readonly_fields = ("reference", "gateway_reference", "created_at", "paid_at")
