from django.contrib import admin

from .models import Announcement, Committee, CommitteeMember, ContactMessage, Department, Executive, Faculty


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
    list_display = ("full_name", "position", "session", "order", "is_current")
    list_filter = ("session", "is_current")
    search_fields = ("full_name", "position")


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
