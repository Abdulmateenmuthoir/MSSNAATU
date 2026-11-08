from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("<slug:slug>/", views.event_detail, name="detail"),
    path("<slug:slug>/register/", views.register, name="register"),
    path("<slug:slug>/cancel/", views.cancel_registration, name="cancel"),
]
