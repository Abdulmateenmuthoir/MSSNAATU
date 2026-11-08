from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.library_list, name="list"),
    path("<int:pk>/", views.question_detail, name="detail"),
    path("<int:pk>/download/", views.question_download, name="download"),
]
