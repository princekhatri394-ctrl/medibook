from django.core.management.base import BaseCommand

from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient

WEEKDAYS = {d: "9:00 AM - 6:00 PM" for d in ["Mon", "Tue", "Wed", "Thu", "Fri"]}
WEEKDAYS["Sat"] = "10:00 AM - 2:00 PM"

DOCTORS = [
    ("Dr. Priya Sharma", "priya@medibook.test", "Cardiologist", 12, 800, "Heart Care Clinic", "Pune", "Baner"),
    ("Dr. Arjun Mehta", "arjun@medibook.test", "Dermatologist", 8, 600, "SkinFirst", "Pune", "Kothrud"),
    ("Dr. Neha Rao", "neha@medibook.test", "Pediatrician", 10, 500, "Little Steps", "Mumbai", "Andheri"),
]


class Command(BaseCommand):
    help = "Create demo admin, doctors and a patient (password: demo1234)."

    def handle(self, *args, **options):
        if not User.objects.filter(email="admin@medibook.test").exists():
            User.objects.create_superuser("admin@medibook.test", "demo1234", name="Admin", phone="0000000000")
        for name, email, spec, exp, fees, clinic, city, area in DOCTORS:
            if User.objects.filter(email=email).exists():
                continue
            user = User.objects.create_user(email, "demo1234", name=name.replace("Dr. ", ""),
                                            phone="9876543210", role=User.Role.DOCTOR)
            Doctor.objects.create(user=user, specialization=spec, experience=exp, fees=fees,
                                  clinic_name=clinic, clinic_address=f"12 Main Road, {area}",
                                  clinic_city=city, clinic_area=area, office_timings=WEEKDAYS,
                                  clinic_desc=f"{spec} with {exp} years of experience.")
        user = User.objects.filter(email="patient@medibook.test").first()
        if user is None:
            user = User.objects.create_user("patient@medibook.test", "demo1234", name="Rahul Verma", phone="9123456780")
        Patient.objects.update_or_create(user=user, defaults={"patient_city": "Pune", "patient_area": "Baner"})
        self.stdout.write(self.style.SUCCESS("Demo data ready. Password for all demo accounts: demo1234"))
