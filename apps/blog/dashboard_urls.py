from django.urls import path

from . import views

app_name = "newsroom"

urlpatterns = [
    path("", views.manage_list, name="list"),
    path("new/", views.post_create, name="create"),
    path("<int:pk>/edit/", views.post_edit, name="edit"),
    path("<int:pk>/delete/", views.post_delete, name="delete"),
    path("comments/", views.comment_list, name="comments"),
    path("comments/<int:pk>/toggle/", views.comment_toggle, name="comment_toggle"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
]
