from django.urls import path

from . import views

app_name = "eventmanager"

urlpatterns = [
    path("", views.manage_list, name="list"),
    path("new/", views.event_create, name="create"),
    path("<int:pk>/edit/", views.event_edit, name="edit"),
    path("<int:pk>/delete/", views.event_delete, name="delete"),
    path("<int:pk>/registrations/", views.registrations, name="registrations"),
    path("<int:pk>/registrations/export/", views.registrations_export, name="registrations_export"),
    path("<int:pk>/registrations/remind/", views.send_reminders, name="remind"),
]
