from django.urls import path

from . import views

app_name = "pastquestions"

urlpatterns = [
    path("", views.manage_list, name="list"),
    path("upload/", views.question_create, name="create"),
    path("<int:pk>/edit/", views.question_edit, name="edit"),
    path("<int:pk>/delete/", views.question_delete, name="delete"),
]
