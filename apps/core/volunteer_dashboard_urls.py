from django.urls import path

from . import views

app_name = "volunteeradmin"

urlpatterns = [
    path("", views.volunteer_applications, name="list"),
    path("<int:pk>/work-sample/", views.volunteer_work_download, name="work_download"),
    path("<int:pk>/status/", views.volunteer_application_status, name="status"),
]
