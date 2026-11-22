from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import models

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

SPECIALIZATIONS = [
    "Cardiologist", "Dermatologist", "Neurologist", "Orthopedic", "Pediatrician",
    "Psychiatrist", "General Physician", "Gynecologist", "Ophthalmologist", "ENT Specialist",
]

TIME_FORMAT = "%I:%M %p"  # e.g. "9:00 AM"
SLOT_MINUTES = 30


def parse_display_time(value):
    return datetime.strptime(value.strip(), TIME_FORMAT).time()


def generate_slots(time_range):
    """'9:00 AM - 6:00 PM' -> [time(9, 0), time(9, 30), ..., time(17, 30)]"""
    open_str, close_str = time_range.split(" - ")
    current = datetime.combine(date.today(), parse_display_time(open_str))
    end = datetime.combine(date.today(), parse_display_time(close_str))
    slots = []
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=SLOT_MINUTES)
    return slots


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor")
    specialization = models.CharField(max_length=100, blank=True)
    experience = models.PositiveIntegerField(default=0)
    fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    clinic_city = models.CharField(max_length=100, blank=True)
    clinic_area = models.CharField(max_length=100, blank=True)
    clinic_name = models.CharField(max_length=150, blank=True)
    clinic_address = models.CharField(max_length=255, blank=True)
    clinic_desc = models.TextField(blank=True)
    # {"Mon": "9:00 AM - 6:00 PM", ...}; missing day = closed
    office_timings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Dr. {self.user.name}"

    @property
    def timing_rows(self):
        return [(day, self.office_timings.get(day)) for day in DAYS]

    def slots_for(self, day):
        time_range = self.office_timings.get(DAYS[day.weekday()])
        return generate_slots(time_range) if time_range else []

    def active_subscription(self):
        return (
            self.subscriptions.select_related("plan")
            .filter(status=DoctorSubscription.Status.ACTIVE, end_date__gte=date.today())
            .order_by("-id")
            .first()
        )


class SubscriptionPlan(models.Model):
    plan_name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    max_appointments = models.PositiveIntegerField(default=10)
    max_specializations = models.PositiveIntegerField(default=1)
    is_featured = models.BooleanField(default=False)
    features = models.TextField(blank=True, help_text="One feature per line")

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.plan_name

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class DoctorSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f"{self.doctor} - {self.plan} ({self.status})"
