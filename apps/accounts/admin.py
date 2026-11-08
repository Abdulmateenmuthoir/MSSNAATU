from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Student


@admin.register(Student)
class StudentAdmin(UserAdmin):
    list_display = ("matric_no", "full_name", "email", "role", "level", "is_active", "must_change_password")
    list_filter = ("role", "gender", "level", "faculty", "is_active")
    search_fields = ("matric_no", "email", "first_name", "last_name")
    ordering = ("last_name", "first_name")
    fieldsets = (
        (None, {"fields": ("matric_no", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "email", "gender", "phone", "bio", "avatar")}),
        ("Academic", {"fields": ("faculty", "department", "level")}),
        ("Access", {"fields": ("role", "is_active", "is_staff", "is_superuser", "must_change_password")}),
        ("Dates", {"fields": ("last_login", "date_joined", "password_set_at", "last_seen")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("matric_no", "email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )
