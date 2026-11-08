from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("executives/", views.executives, name="executives"),
    path("committees/", views.committees, name="committees"),
    path("contact/", views.contact, name="contact"),
    path("health/", views.health, name="health"),
]
