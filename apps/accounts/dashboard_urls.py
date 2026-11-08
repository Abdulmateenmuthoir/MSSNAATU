from django.urls import path

from . import views

app_name = "people"

urlpatterns = [
    path("", views.student_list, name="list"),
    path("add/", views.student_create, name="create"),
    path("credentials/", views.student_credentials, name="credentials"),
    path("import/", views.student_import, name="import"),
    path("import/result/", views.student_import_result, name="import_result"),
    path("promote/", views.promote_levels, name="promote"),
    path("<int:pk>/", views.student_detail, name="detail"),
    path("<int:pk>/resend/", views.student_resend_credentials, name="resend"),
    path("<int:pk>/toggle/", views.student_toggle_active, name="toggle"),
]
