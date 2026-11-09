from django.urls import path

from . import views

app_name = "newsroom"

urlpatterns = [
    path("", views.manage_list, name="list"),
    path("new/", views.post_create, name="create"),
    path("<int:pk>/edit/", views.post_edit, name="edit"),
    path("<int:pk>/delete/", views.post_delete, name="delete"),
    path("comments/", views.comment_list, name="comments"),
    path("subscribers/", views.subscriber_list, name="subscribers"),
    path("subscribers/<int:pk>/toggle/", views.subscriber_toggle, name="subscriber_toggle"),
    path("newsletters/", views.newsletter_list, name="newsletters"),
    path("newsletters/new/", views.newsletter_create, name="newsletter_create"),
    path("newsletters/<int:pk>/edit/", views.newsletter_edit, name="newsletter_edit"),
    path("newsletters/<int:pk>/send/", views.newsletter_send, name="newsletter_send"),
    path("campaigns/<int:pk>/retry/", views.campaign_retry, name="campaign_retry"),
    path("comments/<int:pk>/toggle/", views.comment_toggle, name="comment_toggle"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
]
