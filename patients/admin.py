from django.contrib import admin

from .models import Appointment, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("__str__", "patient_city", "patient_area", "gender", "blood_group")
    search_fields = ("user__name", "user__email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "appointment_date", "time_slot", "status", "created_at")
    list_filter = ("status", "appointment_date")
    search_fields = ("patient__name", "doctor__user__name")
