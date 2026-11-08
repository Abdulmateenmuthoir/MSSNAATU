from django.contrib import admin

from .models import PastQuestion


@admin.register(PastQuestion)
class PastQuestionAdmin(admin.ModelAdmin):
    list_display = ("course_code", "course_title", "department", "level", "session", "downloads")
    list_filter = ("faculty", "department", "level", "session")
    search_fields = ("course_code", "course_title")
