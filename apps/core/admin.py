from django.contrib import admin

from .models import (
    Announcement,
    Committee,
    CommitteeMember,
    ContactMessage,
    Department,
    Executive,
    Faculty,
    NewsletterSubscriber,
    VolunteerApplication,
)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "faculty", "order")
    list_filter = ("faculty",)
    search_fields = ("name", "code")


class CommitteeMemberInline(admin.TabularInline):
    model = CommitteeMember
    extra = 1


@admin.register(Executive)
class ExecutiveAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "avatar_icon", "department", "department_label", "level", "phone", "session", "is_current")
    list_filter = ("session", "is_current", "avatar_icon", "level", "department__faculty")
    search_fields = ("full_name", "position", "phone", "department__name", "department_label")


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = ("name", "session", "order")
    list_filter = ("session",)
    inlines = [CommitteeMemberInline]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at", "is_resolved")
    list_filter = ("is_resolved",)
    search_fields = ("name", "email", "subject", "message")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_active", "subscribed_at")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email", "name")


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "team", "team_role", "status", "created_at")
    list_filter = ("team", "status", "created_at")
    search_fields = ("student__first_name", "student__last_name", "student__matric_no", "student__email")
    readonly_fields = ("student", "created_at", "updated_at")
