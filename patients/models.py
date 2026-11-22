from django.conf import settings
from django.db import models
from django.db.models import Q

from doctors.models import Doctor


class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    patient_city = models.CharField(max_length=100, blank=True)
    patient_area = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.name


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    appointment_date = models.DateField()
    time_slot = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-appointment_date", "-time_slot"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "time_slot"],
                condition=~Q(status="cancelled"),
                name="unique_active_booking_per_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient.name} with {self.doctor} on {self.appointment_date} {self.time_slot}"
