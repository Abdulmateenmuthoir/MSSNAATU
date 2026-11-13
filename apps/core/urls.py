from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("executives/", views.executives, name="executives"),
    path("branches/", views.branches, name="branches"),
    path("committees/", views.committees, name="committees"),
    path("contact/", views.contact, name="contact"),
    path("volunteer/", views.volunteer_apply, name="volunteer"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("health/", views.health, name="health"),
]
