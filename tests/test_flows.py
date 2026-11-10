from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from doctors.models import Doctor, DoctorSubscription, SubscriptionPlan
from patients.models import Appointment

ALL_DAYS = {d: "9:00 AM - 6:00 PM" for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}


class FlowTests(TestCase):
    def setUp(self):
        self.doc_user = User.objects.create_user("doc@test.com", "secret123x", name="House", phone="111", role="doctor")
        self.doctor = Doctor.objects.create(user=self.doc_user, specialization="Cardiologist", fees=500,
                                            clinic_name="City Care", clinic_city="Pune", office_timings=ALL_DAYS)
        self.pat = User.objects.create_user("pat@test.com", "secret123x", name="Asha", phone="222")
        self.tomorrow = date.today() + timedelta(days=1)

    def test_register_patient_then_location_then_dashboard(self):
        r = self.client.post(reverse("accounts:register"), {
            "name": "New P", "email": "NEW@test.com", "phone": "333", "password": "goodpass99",
            "confirm_password": "goodpass99", "role": "patient"})
        self.assertRedirects(r, reverse("patients:location"))
        r = self.client.post(reverse("patients:location"), {"city": "Pune", "area": "Baner"})
        self.assertRedirects(r, reverse("patients:dashboard"))
        r = self.client.get(reverse("patients:dashboard") + "?tab=doctors")
        self.assertContains(r, "Dr. House")
        self.assertContains(r, "Same City")

    def test_register_doctor_full_onboarding(self):
        r = self.client.post(reverse("accounts:register"), {
            "name": "Strange", "email": "s@test.com", "phone": "444", "password": "goodpass99",
            "confirm_password": "goodpass99", "role": "doctor", "specialization": "Neurologist",
            "experience": 7, "fees": 800})
        self.assertRedirects(r, reverse("doctors:location"))
        r = self.client.post(reverse("doctors:location"), {"city": "Mumbai", "area": "Bandra"})
        self.assertRedirects(r, reverse("doctors:clinic_details"))
        r = self.client.post(reverse("doctors:clinic_details"), {
            "clinic_name": "Sanctum", "clinic_address": "177A Bleecker", "clinic_desc": "",
            "day_Mon": "on", "open_Mon": "9:00 AM", "close_Mon": "1:00 PM"})
        self.assertRedirects(r, reverse("doctors:select_plan"))
        plan = SubscriptionPlan.objects.get(plan_name="Standard")
        r = self.client.post(reverse("doctors:select_plan"), {"plan_id": plan.id})
        self.assertRedirects(r, reverse("doctors:dashboard"))
        doc = Doctor.objects.get(user__email="s@test.com")
        self.assertEqual(doc.office_timings, {"Mon": "9:00 AM - 1:00 PM"})
        self.assertEqual(doc.active_subscription().plan, plan)
        r = self.client.get(reverse("doctors:dashboard"))
        self.assertContains(r, "Standard Plan")

    def test_duplicate_email_and_password_mismatch(self):
        data = {"name": "X", "email": "pat@test.com", "phone": "1", "password": "goodpass99",
                "confirm_password": "goodpass99", "role": "patient"}
        self.assertContains(self.client.post(reverse("accounts:register"), data), "already registered")
        data.update(email="x@test.com", confirm_password="other")
        self.assertContains(self.client.post(reverse("accounts:register"), data), "Passwords do not match")

    def test_login_redirects_by_role(self):
        r = self.client.post(reverse("accounts:login"), {"email": "DOC@test.com", "password": "secret123x"})
        self.assertRedirects(r, reverse("doctors:dashboard"))
        self.client.get(reverse("accounts:logout"))
        r = self.client.post(reverse("accounts:login"), {"email": "pat@test.com", "password": "wrong"})
        self.assertContains(r, "Invalid email or password")

    def test_role_protection(self):
        self.client.force_login(self.pat)
        self.assertRedirects(self.client.get(reverse("doctors:dashboard")), reverse("patients:dashboard"))
        self.client.logout()
        r = self.client.get(reverse("patients:dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("accounts:login"), r.url)

    def test_booking_rules(self):
        self.client.force_login(self.pat)
        url = reverse("patients:book_appointment", args=[self.doctor.id])
        r = self.client.post(url, {"appointment_date": self.tomorrow.isoformat(), "time_slot": "10:00:00"})
        self.assertContains(r, "Appointment Booked!")
        r = self.client.post(url, {"appointment_date": self.tomorrow.isoformat(), "time_slot": "10:00:00"})
        self.assertContains(r, "already booked")
        r = self.client.post(url, {"appointment_date": self.tomorrow.isoformat(), "time_slot": "20:00:00"})
        self.assertContains(r, "not available")
        r = self.client.post(url, {"appointment_date": (date.today() - timedelta(days=2)).isoformat(),
                                   "time_slot": "10:00:00"})
        self.assertContains(r, "in the past")
        r = self.client.get(reverse("patients:booked_slots", args=[self.doctor.id]),
                            {"date": self.tomorrow.isoformat()})
        self.assertEqual(r.json(), ["10:00:00"])

    def test_closed_day_rejected(self):
        self.doctor.office_timings = {"Mon": "9:00 AM - 6:00 PM"}
        self.doctor.save()
        day = self.tomorrow
        while day.weekday() == 0:
            day += timedelta(days=1)
        self.client.force_login(self.pat)
        r = self.client.post(reverse("patients:book_appointment", args=[self.doctor.id]),
                             {"appointment_date": day.isoformat(), "time_slot": "10:00:00"})
        self.assertContains(r, "not available")

    def test_cancel_and_status_update(self):
        appt = Appointment.objects.create(patient=self.pat, doctor=self.doctor,
                                          appointment_date=self.tomorrow, time_slot=time(10))
        self.client.force_login(self.doc_user)
        self.client.post(reverse("doctors:update_status", args=[appt.id]), {"new_status": "hacked"})
        appt.refresh_from_db()
        self.assertEqual(appt.status, "pending")
        self.client.post(reverse("doctors:update_status", args=[appt.id]), {"new_status": "confirmed"})
        appt.refresh_from_db()
        self.assertEqual(appt.status, "confirmed")
        self.client.force_login(self.pat)
        self.client.post(reverse("patients:cancel_appointment", args=[appt.id]))
        appt.refresh_from_db()
        self.assertEqual(appt.status, "cancelled")
        r = self.client.get(reverse("patients:dashboard") + "?tab=appointments")
        self.assertContains(r, "Cancelled")

    def test_other_patient_cannot_cancel(self):
        appt = Appointment.objects.create(patient=self.pat, doctor=self.doctor,
                                          appointment_date=self.tomorrow, time_slot=time(10))
        other = User.objects.create_user("o@test.com", "secret123x", name="O", phone="5")
        self.client.force_login(other)
        r = self.client.post(reverse("patients:cancel_appointment", args=[appt.id]))
        self.assertEqual(r.status_code, 404)

    def test_pages_render(self):
        self.client.force_login(self.doc_user)
        for name in ["doctors:location", "doctors:clinic_details", "doctors:select_plan",
                     "doctors:edit_profile", "doctors:dashboard"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        r = self.client.post(reverse("doctors:edit_profile"), {"name": "House MD", "phone": "999",
                             "specialization": "Cardiologist", "experience": 20, "fees": 900, "bio": ""})
        self.assertRedirects(r, reverse("doctors:dashboard"))
        self.client.force_login(self.pat)
        for name in ["patients:location", "patients:dashboard", "patients:edit_profile"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("patients:book_appointment", args=[self.doctor.id])).status_code, 200)
