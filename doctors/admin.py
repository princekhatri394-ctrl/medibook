from django.contrib import admin

from .models import Doctor, DoctorSubscription, SubscriptionPlan


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "specialization", "experience", "fees", "clinic_name", "clinic_city", "clinic_area")
    list_filter = ("specialization", "clinic_city")
    search_fields = ("user__name", "user__email", "clinic_name")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("plan_name", "price", "duration_days", "max_appointments", "is_featured")


@admin.register(DoctorSubscription)
class DoctorSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("doctor", "plan", "start_date", "end_date", "status")
    list_filter = ("status", "plan")
