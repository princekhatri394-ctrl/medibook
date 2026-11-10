from datetime import date, time

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.decorators import role_required
from accounts.forms import UserProfileForm, first_error
from doctors.models import DAYS, Doctor

from .forms import PatientProfileForm
from .models import Appointment, Patient


def _get_patient(request):
    patient, _ = Patient.objects.get_or_create(user=request.user)
    return patient


@role_required("patient")
def location(request):
    patient = _get_patient(request)
    if request.method == "POST" and request.POST.get("city"):
        city = request.POST["city"].strip()[:100]
        patient.patient_city = "" if city == "All" else city
        patient.patient_area = "" if city == "All" else request.POST.get("area", "").strip()[:100]
        patient.save(update_fields=["patient_city", "patient_area"])
        return redirect("patients:dashboard")
    return render(request, "patients/location.html")


@role_required("patient")
def dashboard(request):
    patient = _get_patient(request)
    city = patient.patient_city or "All"
    area = patient.patient_area

    doctors = list(
        Doctor.objects.select_related("user")
        .annotate(
            name=F("user__name"), email=F("user__email"), phone=F("user__phone"),
            proximity=Case(
                When(Q(clinic_area=area, clinic_city=city) & ~Q(clinic_area=""), then=Value(1)),
                When(clinic_city=city, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
        )
        .order_by("proximity", "-experience")
    )
    today_key = DAYS[timezone.localdate().weekday()]
    for doc in doctors:
        doc.today_timing = doc.office_timings.get(today_key)
        if area and doc.clinic_area == area:
            doc.dist_label, doc.dist_class = "📍 Same Area", "near"
        elif doc.clinic_city == city:
            doc.dist_label, doc.dist_class = "🏙️ Same City", "city"
        else:
            doc.dist_label, doc.dist_class = "📌 " + (doc.clinic_city or "Other City"), "far"

    appointments = list(
        request.user.appointments.annotate(
            doctor_name=F("doctor__user__name"), specialization=F("doctor__specialization"),
            clinic_name=F("doctor__clinic_name"), clinic_address=F("doctor__clinic_address"),
        )
    )
    today = timezone.localdate()
    upcoming = [a for a in appointments
                if a.appointment_date >= today and a.status != Appointment.Status.CANCELLED]

    context = {
        "patient": request.user,
        "patient_city": city,
        "patient_area": area,
        "location_label": area or city,
        "location_full": f"{area}, {city}" if area else city,
        "tab": request.GET.get("tab", "profile"),
        "doctors": doctors,
        "appointments": appointments,
        "total_appts": len(appointments),
        "upcoming_appts": upcoming,
        "pending_appts": [a for a in appointments if a.status == Appointment.Status.PENDING],
        "completed_count": sum(a.status == Appointment.Status.COMPLETED for a in appointments),
    }
    return render(request, "patients/dashboard.html", context)


@require_POST
@role_required("patient")
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    if appointment.status in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED):
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status"])
        messages.success(request, "Appointment cancelled.")
    return redirect(reverse("patients:dashboard") + "?tab=appointments")


def _booking_error(doctor, day, slot):
    now = timezone.localtime()
    if day < now.date():
        return "You can't book an appointment in the past."
    if slot not in doctor.slots_for(day):
        return "The doctor is not available at that time. Please choose another slot."
    if day == now.date() and slot <= now.time():
        return "That time has already passed. Please choose a later slot."
    return ""


@role_required("patient")
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(
        Doctor.objects.select_related("user").annotate(name=F("user__name"), phone=F("user__phone")), pk=doctor_id
    )
    error = ""
    success = False

    if request.method == "POST":
        try:
            day = date.fromisoformat(request.POST.get("appointment_date", ""))
            slot = time.fromisoformat(request.POST.get("time_slot", ""))
        except ValueError:
            error = "Please select a date and time slot."
        else:
            error = _booking_error(doctor, day, slot)
            if not error:
                try:
                    with transaction.atomic():
                        taken = (Appointment.objects.select_for_update()
                                 .filter(doctor=doctor, appointment_date=day, time_slot=slot)
                                 .exclude(status=Appointment.Status.CANCELLED).exists())
                        if taken:
                            error = "This slot is already booked. Please choose another."
                        else:
                            Appointment.objects.create(
                                patient=request.user, doctor=doctor, appointment_date=day,
                                time_slot=slot, reason=request.POST.get("reason", "").strip()[:1000],
                            )
                            success = True
                except IntegrityError:
                    error = "This slot is already booked. Please choose another."

    return render(request, "patients/book_appointment.html", {
        "doctor": doctor, "error": error, "success": success,
        "timings": doctor.office_timings, "timing_rows": doctor.timing_rows,
    })


@require_GET
@role_required("patient")
def booked_slots(request, doctor_id):
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    try:
        day = date.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        return JsonResponse([], safe=False)
    taken = (Appointment.objects.filter(doctor=doctor, appointment_date=day)
             .exclude(status=Appointment.Status.CANCELLED)
             .values_list("time_slot", flat=True))
    return JsonResponse([t.strftime("%H:%M:%S") for t in taken], safe=False)


@role_required("patient")
def edit_profile(request):
    patient = _get_patient(request)
    user_form = UserProfileForm(request.POST or None, instance=request.user)
    patient_form = PatientProfileForm(request.POST or None, instance=patient)
    error = ""
    if request.method == "POST":
        if user_form.is_valid() and patient_form.is_valid():
            user_form.save()
            patient_form.save()
            messages.success(request, "Profile updated.")
            return redirect("patients:dashboard")
        error = first_error(user_form) or first_error(patient_form)
    return render(request, "edit_profile.html", {
        "forms": [user_form, patient_form], "error": error,
        "back_url": "patients:dashboard", "greeting": request.user.name,
    })
