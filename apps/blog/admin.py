from django.contrib import admin

from .models import Comment, NewsEmailCampaign, NewsletterCampaign, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_published", "published_at", "views")
    list_filter = ("is_published", "category")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "is_visible", "created_at")
    list_filter = ("is_visible",)
    search_fields = ("body", "author__first_name", "author__last_name")


@admin.register(NewsEmailCampaign)
class NewsEmailCampaignAdmin(admin.ModelAdmin):
    list_display = ("post", "status", "recipient_count", "sent_at", "created_at")
    list_filter = ("status",)
    readonly_fields = ("post", "status", "recipient_count", "sent_at", "last_error", "created_at")


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "recipient_count", "created_at", "sent_at")
    list_filter = ("status",)
    search_fields = ("title", "preview", "content")
