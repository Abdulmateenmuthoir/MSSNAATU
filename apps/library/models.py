import os

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.core.models import Department, Faculty, LEVEL_CHOICES


def question_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"past-questions/{instance.faculty.code}/{instance.department.code}/{instance.level}/{instance.course_code}{ext}"


class PastQuestion(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="past_questions")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="past_questions")
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, db_index=True)
    course_code = models.CharField(max_length=16, db_index=True)
    course_title = models.CharField(max_length=180)
    session = models.CharField(max_length=40, help_text="e.g. 2024/2025")
    file = models.FileField(upload_to=question_upload_path)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_questions"
    )
    downloads = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("course_code", "session", "department", "level")]

    def __str__(self):
        return f"{self.course_code} — {self.session}"

    @property
    def extension(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext.replace(".", "") or "file"

    @property
    def download_url(self):
        return reverse("library:download", args=[self.pk])
