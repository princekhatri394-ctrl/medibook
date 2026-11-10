from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [
    path("location/", views.location, name="location"),
    path("clinic-details/", views.clinic_details, name="clinic_details"),
    path("select-plan/", views.select_plan, name="select_plan"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("appointments/<int:appointment_id>/status/", views.update_appointment_status, name="update_status"),
]
