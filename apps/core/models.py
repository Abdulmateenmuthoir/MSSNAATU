from django.db import models
from django.urls import reverse
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


def society_url():
    return reverse("core:home")
