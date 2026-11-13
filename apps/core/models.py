import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify

LEVEL_CHOICES = [
    ("100", "100 Level"),
    ("200", "200 Level"),
    ("300", "300 Level"),
    ("400", "400 Level"),
    ("500", "500 Level"),
    ("600", "600 Level"),
    ("700", "700 Level"),
]

EXECUTIVE_ICON_CHOICES = [("male", "Male profile icon"), ("female", "Female profile icon")]

VOLUNTEER_TEAM_CHOICES = [
    ("it_media_team", "IT and Media Team"),
    ("educational_committee", "Educational Committee"),
    ("editorial_board", "Editorial Board"),
    ("business_committee", "Business Committee (legacy application)"),
]
VOLUNTEER_FORM_TEAM_CHOICES = VOLUNTEER_TEAM_CHOICES[:3]
VOLUNTEER_ROLE_CHOICES_BY_TEAM = {
    "it_media_team": [
        ("graphics_designer", "Graphics Designer"),
        ("videographer", "Video Grapher"),
        ("video_editor", "Video Editor"),
        ("it_content_creator", "Content Creator"),
    ],
    "educational_committee": [("tutor", "Tutor")],
    "editorial_board": [
        ("editorial_content_creator", "Content Creator"),
        ("article_writer", "Article Writer"),
    ],
    "business_committee": [("legacy_role", "Legacy application")],
}
VOLUNTEER_ROLE_CHOICES = [
    choice for role_choices in VOLUNTEER_ROLE_CHOICES_BY_TEAM.values() for choice in role_choices
]
VOLUNTEER_ROLE_GROUP_CHOICES = [
    (label, VOLUNTEER_ROLE_CHOICES_BY_TEAM[team])
    for team, label in VOLUNTEER_FORM_TEAM_CHOICES
]
VOLUNTEER_COURSE_CHOICES = [
    ("GET 201", "GET 201"),
    ("GET 205", "GET 205"),
    ("GET 207", "GET 207"),
    ("MTH 201", "MTH 201"),
]
VOLUNTEER_STATUS_CHOICES = [
    ("pending", "Pending review"),
    ("reviewing", "Under review"),
    ("accepted", "Accepted"),
    ("declined", "Declined"),
]
VOLUNTEER_WORK_MAX_BYTES = 10 * 1024 * 1024
VOLUNTEER_WORK_EXTENSIONS = ["pdf", "doc", "docx", "ppt", "pptx", "zip", "jpg", "jpeg", "png", "webp", "mp4", "mov"]


def validate_volunteer_work_size(file):
    if file.size > VOLUNTEER_WORK_MAX_BYTES:
        raise ValidationError("The work sample must be 10 MB or smaller.")


def volunteer_work_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    return f"volunteer-work/{uuid.uuid4().hex}{extension}"


@deconstructible
class VolunteerWorkStorage(FileSystemStorage):
    """Keep applicant work samples outside publicly served media files."""

    def __init__(self):
        super().__init__(location=settings.BASE_DIR / "private_uploads")


class Faculty(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=12, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Faculties"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=140)
    code = models.CharField(max_length=12)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")
    slug = models.SlugField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["faculty__name", "name"]
        unique_together = [("faculty", "name")]
        verbose_name_plural = "Departments"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.faculty.code}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.faculty.code})"


class Executive(models.Model):
    full_name = models.CharField(max_length=140)
    position = models.CharField(max_length=120)
    session = models.CharField(max_length=40, db_index=True)
    photo = models.ImageField(upload_to="executives/", blank=True)
    bio = models.TextField(blank=True, max_length=800)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    avatar_icon = models.CharField(
        "fallback profile icon",
        max_length=6,
        choices=EXECUTIVE_ICON_CHOICES,
        blank=True,
        default="",
        help_text="Shown when no executive photo is uploaded. Choose the matching illustration.",
    )
    department = models.ForeignKey(
        "Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="executives"
    )
    department_label = models.CharField(
        "department as supplied", max_length=140, blank=True,
        help_text="Preserves the executive's department when it has not yet been added to the department directory.",
    )
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "full_name"]
        unique_together = [("full_name", "position", "session")]

    def __str__(self):
        return f"{self.full_name} — {self.position}"

    @property
    def initials(self):
        parts = [part for part in self.full_name.split() if part]
        return "".join(part[0] for part in parts[:2]).upper()


class Committee(models.Model):
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    session = models.CharField(max_length=40, db_index=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        unique_together = [("name", "session")]

    def __str__(self):
        return self.name


class CommitteeMember(models.Model):
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name="members")
    full_name = models.CharField(max_length=140)
    role = models.CharField(max_length=120, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "full_name"]

    def __str__(self):
        return self.full_name


class Announcement(models.Model):
    title = models.CharField(max_length=180)
    body = models.TextField(max_length=800)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=160)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"


class NewsletterSubscriber(models.Model):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.name or self.email


class VolunteerApplication(models.Model):
    PENDING = "pending"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    DECLINED = "declined"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_applications",
    )
    team = models.CharField(max_length=32, choices=VOLUNTEER_TEAM_CHOICES)
    team_role = models.CharField(max_length=32, choices=VOLUNTEER_ROLE_CHOICES, default="legacy_role")
    courses = models.JSONField(default=list, blank=True)
    work_sample = models.FileField(
        upload_to=volunteer_work_path,
        storage=VolunteerWorkStorage(),
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=VOLUNTEER_WORK_EXTENSIONS),
            validate_volunteer_work_size,
        ],
    )
    publication_url = models.URLField(max_length=500, blank=True)
    has_no_publication = models.BooleanField(default=False)
    message = models.TextField(max_length=1200, blank=True)
    status = models.CharField(max_length=12, choices=VOLUNTEER_STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "team", "team_role"],
                name="unique_volunteer_application_per_team_role",
            )
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.get_team_display()}"


def society_url():
    return reverse("core:home")
