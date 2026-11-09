from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

ELIGIBILITY_ALL = "all"
ELIGIBILITY_BROTHERS = "brothers"
ELIGIBILITY_SISTERS = "sisters"
ELIGIBILITY_CHOICES = [
    (ELIGIBILITY_ALL, "Everyone"),
    (ELIGIBILITY_BROTHERS, "Brothers only"),
    (ELIGIBILITY_SISTERS, "Sisters only"),
]

ELIGIBILITY_GENDER = {
    ELIGIBILITY_ALL: None,
    ELIGIBILITY_BROTHERS: "M",
    ELIGIBILITY_SISTERS: "F",
}

PROGRAM_FREQUENCY_CHOICES = [
    ("weekly", "Weekly"),
    ("fortnightly", "Fortnightly"),
    ("monthly", "Monthly"),
    ("semester", "At least once each semester"),
    ("annual", "Annual / once each session"),
    ("periodic", "Regular or periodic"),
    ("scheduled", "As scheduled by the Executive Council"),
]


class Program(models.Model):
    name = models.CharField(max_length=160, unique=True)
    summary = models.CharField(max_length=280)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=16, choices=PROGRAM_FREQUENCY_CHOICES, default="scheduled")
    coordinator = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.CharField(max_length=280, help_text="A short line for cards and previews.")
    description = models.TextField(help_text="Markdown is supported.")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=180)
    flyer = models.ImageField(upload_to="events/", blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave empty for no limit.")
    eligibility = models.CharField(max_length=12, choices=ELIGIBILITY_CHOICES, default=ELIGIBILITY_ALL)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_events"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:180] or "event"
            slug = base
            counter = 2
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("events:detail", args=[self.slug])

    @property
    def flyer_url(self):
        return self.flyer.url if self.flyer else ""

    @property
    def is_past(self):
        return self.starts_at < timezone.now()

    @property
    def registration_open(self):
        if not self.is_published or self.is_past:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        if self.capacity is not None and self.registrations.count() >= self.capacity:
            return False
        return True

    @property
    def spots_left(self):
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.registrations.count())

    @property
    def is_full(self):
        return self.capacity is not None and self.registrations.count() >= self.capacity

    def eligible_for(self, student):
        required_gender = ELIGIBILITY_GENDER.get(self.eligibility)
        if required_gender is None:
            return True
        return bool(student and student.is_authenticated and student.gender == required_gender)

    @property
    def eligibility_short(self):
        return {
            ELIGIBILITY_ALL: "Open to all",
            ELIGIBILITY_BROTHERS: "Brothers only",
            ELIGIBILITY_SISTERS: "Sisters only",
        }[self.eligibility]


class Registration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = [("event", "student")]

    def __str__(self):
        return f"{self.student.full_name} → {self.event.title}"
