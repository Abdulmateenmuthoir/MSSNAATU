from django.urls import path

from . import views

app_name = "programmeadmin"

urlpatterns = [
    path("", views.program_manage_list, name="list"),
    path("new/", views.program_create, name="create"),
    path("<int:pk>/edit/", views.program_edit, name="edit"),
    path("<int:pk>/delete/", views.program_delete, name="delete"),
]
