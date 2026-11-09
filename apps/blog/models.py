import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

CATEGORY_CHOICES = [
    ("news", "News"),
    ("editorial", "Editorial"),
    ("campus", "Campus"),
    ("deen", "Deen"),
    ("society", "Society"),
]


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="news")
    excerpt = models.CharField(max_length=280, help_text="One or two sentences shown on cards and previews.")
    content = models.TextField(help_text="Markdown is supported: **bold**, lists, links and quotes.")
    cover = models.ImageField(upload_to="news/", blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posts")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "story"
            slug = base
            counter = 2
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", args=[self.slug])

    @property
    def reading_time(self):
        words = len(re.findall(r"\w+", self.content))
        return max(1, round(words / 220))

    @property
    def cover_url(self):
        return self.cover.url if self.cover else ""


class NewsEmailCampaign(models.Model):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    STATUS_CHOICES = [(QUEUED, "Queued"), (SENT, "Sent"), (FAILED, "Failed")]
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="email_campaign")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=QUEUED)
    recipient_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class NewsletterCampaign(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"
    STATUS_CHOICES = [(DRAFT, "Draft"), (SENT, "Sent"), (FAILED, "Failed")]

    title = models.CharField(max_length=180)
    preview = models.CharField(max_length=280, blank=True)
    content = models.TextField(help_text="Markdown is supported.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="newsletter_campaigns"
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=DRAFT)
    recipient_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField(max_length=1500)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.short_name} on {self.post.title}"
