import secrets
import string

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Department, Faculty, LEVEL_CHOICES

ROLE_SUPER = "super_admin"
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_EVENTS = "events"
ROLE_FINANCE = "finance"
ROLE_LIBRARY = "library"
ROLE_MEMBER = "member"

ROLE_CHOICES = [
    (ROLE_SUPER, "Super User"),
    (ROLE_ADMIN, "Administrator"),
    (ROLE_EDITOR, "Content Editor"),
    (ROLE_EVENTS, "Events Manager"),
    (ROLE_FINANCE, "Finance Officer"),
    (ROLE_LIBRARY, "Past Questions Manager"),
    (ROLE_MEMBER, "Member"),
]

GENDER_CHOICES = [("M", "Brother"), ("F", "Sister")]

MATRIC_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9/\-\.]+$",
    message="Use letters, numbers, slashes, dots or hyphens only.",
)


def generate_temp_password(length=12):
    """A readable but strong one-time password, e.g. Mssn-K7p2-Qr9t."""
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"Mssn-{body[:4]}-{body[4:8]}"


class StudentManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, matric_no, email, password, **extra_fields):
        if not matric_no:
            raise ValueError("A matric number is required.")
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        matric_no = matric_no.strip().upper()
        user = self.model(matric_no=matric_no, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, matric_no, email, password=None, **extra_fields):
        extra_fields.setdefault("role", ROLE_MEMBER)
        extra_fields.setdefault("is_active", True)
        return self._create_user(matric_no, email, password, **extra_fields)

    def create_superuser(self, matric_no, email, password=None, **extra_fields):
        extra_fields.setdefault("role", ROLE_SUPER)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("must_change_password", False)
        return self._create_user(matric_no, email, password, **extra_fields)


class Student(AbstractBaseUser, PermissionsMixin):
    matric_no = models.CharField(
        "matric number",
        max_length=32,
        unique=True,
        validators=[MATRIC_VALIDATOR],
        help_text="The unique student ID, e.g. AATU/CS/22/001.",
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    must_change_password = models.BooleanField(
        default=True,
        help_text="Prompt the student to replace their temporary password at next login.",
    )
    password_set_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(null=True, blank=True)

    objects = StudentManager()

    USERNAME_FIELD = "matric_no"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "student"
        verbose_name_plural = "students"

    def __str__(self):
        return f"{self.full_name} ({self.matric_no})"

    def save(self, *args, **kwargs):
        self.matric_no = (self.matric_no or "").strip().upper()
        self.email = (self.email or "").strip().lower()
        if self.role == ROLE_SUPER:
            self.is_superuser = True
            self.is_staff = True
        elif self.role != ROLE_MEMBER:
            self.is_staff = True
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("accounts:profile")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def short_name(self):
        return self.first_name or self.full_name

    @property
    def initials(self):
        return "".join(part[0] for part in [self.first_name, self.last_name] if part).upper() or "?"

    @property
    def role_label(self):
        return self.get_role_display()

    @property
    def is_super_admin(self):
        return self.role == ROLE_SUPER or self.is_superuser

    @property
    def is_administrator(self):
        return self.is_super_admin or self.role == ROLE_ADMIN

    @property
    def can_manage_people(self):
        return self.is_administrator

    @property
    def can_manage_content(self):
        return self.is_administrator or self.role == ROLE_EDITOR

    @property
    def can_manage_events(self):
        return self.is_administrator or self.role == ROLE_EVENTS

    @property
    def can_manage_finance(self):
        return self.is_administrator or self.role == ROLE_FINANCE

    @property
    def can_manage_library(self):
        return self.is_administrator or self.role == ROLE_LIBRARY

    @property
    def academic_summary(self):
        bits = [self.get_level_display()] if self.level else []
        if self.department:
            bits.append(self.department.name)
        elif self.faculty:
            bits.append(self.faculty.name)
        return " · ".join(bits) or "No academic details yet"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return ""
