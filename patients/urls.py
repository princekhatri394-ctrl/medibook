from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("location/", views.location, name="location"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("book/<int:doctor_id>/", views.book_appointment, name="book_appointment"),
    path("book/<int:doctor_id>/slots/", views.booked_slots, name="booked_slots"),
    path("appointments/<int:appointment_id>/cancel/", views.cancel_appointment, name="cancel_appointment"),
]
