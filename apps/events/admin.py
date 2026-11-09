from django.contrib import admin

from .models import Event, Program, Registration


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "frequency", "coordinator", "is_active", "order")
    list_filter = ("is_active", "frequency")
    search_fields = ("name", "summary", "description", "coordinator")


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    readonly_fields = ("student", "created_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "venue", "eligibility", "capacity", "is_published")
    list_filter = ("is_published", "eligibility", "starts_at")
    search_fields = ("title", "summary", "venue")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("student", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("student__first_name", "student__last_name", "student__matric_no")
