from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.forms import UserProfileForm, first_error
from patients.models import Appointment

from .forms import DoctorProfileForm
from .models import DAYS, Doctor, DoctorSubscription, SubscriptionPlan, parse_display_time


def _get_doctor(request):
    doctor, _ = Doctor.objects.get_or_create(user=request.user)
    return doctor


@role_required("doctor")
def location(request):
    doctor = _get_doctor(request)
    if request.method == "POST":
        city = request.POST.get("city", "").strip()[:100]
        area = request.POST.get("area", "").strip()[:100]
        if city and city != "All":
            doctor.clinic_city = city
            doctor.clinic_area = area
            doctor.save(update_fields=["clinic_city", "clinic_area"])
        if not doctor.clinic_name:
            return redirect("doctors:clinic_details")
        return redirect("doctors:dashboard")
    return render(request, "doctors/location.html")


def _parse_timings(post):
    """Return ({day: 'open - close'}, error)."""
    timings = {}
    for day in DAYS:
        if not post.get(f"day_{day}"):
            continue
        open_str, close_str = post.get(f"open_{day}", ""), post.get(f"close_{day}", "")
        try:
            open_t, close_t = parse_display_time(open_str), parse_display_time(close_str)
        except ValueError:
            return timings, f"Invalid time selected for {day}."
        if open_t >= close_t:
            return timings, f"Closing time must be after opening time on {day}."
        timings[day] = f"{open_str.strip()} - {close_str.strip()}"
    return timings, ""


@role_required("doctor")
def clinic_details(request):
    doctor = _get_doctor(request)
    error = ""
    values = {"clinic_name": doctor.clinic_name, "clinic_address": doctor.clinic_address,
              "clinic_desc": doctor.clinic_desc}
    timings = doctor.office_timings

    if request.method == "POST":
        values = {k: request.POST.get(k, "").strip() for k in values}
        timings, error = _parse_timings(request.POST)
        if not error:
            if not values["clinic_name"]:
                error = "Please enter your clinic name."
            elif not values["clinic_address"]:
                error = "Please enter your clinic address."
            elif not timings:
                error = "Please select at least one working day with timings."
        if not error:
            doctor.clinic_name = values["clinic_name"][:150]
            doctor.clinic_address = values["clinic_address"][:255]
            doctor.clinic_desc = values["clinic_desc"][:300]
            doctor.office_timings = timings
            doctor.save()
            if doctor.active_subscription():
                messages.success(request, "Clinic details saved.")
                return redirect("doctors:dashboard")
            return redirect("doctors:select_plan")

    return render(request, "doctors/clinic_details.html",
                  {"error": error, "values": values, "timings": timings})


@role_required("doctor")
def select_plan(request):
    doctor = _get_doctor(request)
    plans = SubscriptionPlan.objects.all()
    current = doctor.active_subscription()

    if request.method == "POST":
        plan = get_object_or_404(SubscriptionPlan, pk=request.POST.get("plan_id"))
        with transaction.atomic():
            doctor.subscriptions.filter(status=DoctorSubscription.Status.ACTIVE).update(
                status=DoctorSubscription.Status.CANCELLED
            )
            DoctorSubscription.objects.create(
                doctor=doctor, plan=plan, start_date=date.today(),
                end_date=date.today() + timedelta(days=plan.duration_days),
            )
        messages.success(request, f"You're now on the {plan.plan_name} plan.")
        return redirect("doctors:dashboard")

    return render(request, "doctors/select_plan.html", {"plans": plans, "current": current})


@role_required("doctor")
def dashboard(request):
    _get_doctor(request)
    doctor = (
        Doctor.objects.annotate(name=F("user__name"), email=F("user__email"), phone=F("user__phone"))
        .get(user=request.user)
    )
    subscription = doctor.active_subscription()
    appointments = list(
        doctor.appointments.annotate(
            patient_name=F("patient__name"), patient_phone=F("patient__phone"), patient_email=F("patient__email")
        )
    )
    today = date.today()
    pending = [a for a in appointments if a.status == Appointment.Status.PENDING]
    context = {
        "doctor": doctor,
        "subscription": subscription,
        "appointments": appointments,
        "total_appts": len(appointments),
        "today_appts": [a for a in appointments if a.appointment_date == today],
        "pending_appts": pending,
        "completed_appts": [a for a in appointments if a.status == Appointment.Status.COMPLETED],
        "tab": request.GET.get("tab", "profile"),
        "timings": doctor.office_timings,
        "status_choices": Appointment.Status.choices,
    }
    return render(request, "doctors/dashboard.html", context)


@require_POST
@role_required("doctor")
def update_appointment_status(request, appointment_id):
    doctor = _get_doctor(request)
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=doctor)
    new_status = request.POST.get("new_status")
    if new_status in Appointment.Status.values:
        appointment.status = new_status
        appointment.save(update_fields=["status"])
        messages.success(request, "Appointment updated.")
    else:
        messages.error(request, "Invalid status.")
    return redirect(reverse("doctors:dashboard") + "?tab=appointments")


@role_required("doctor")
def edit_profile(request):
    doctor = _get_doctor(request)
    user_form = UserProfileForm(request.POST or None, instance=request.user)
    doctor_form = DoctorProfileForm(request.POST or None, instance=doctor)
    error = ""
    if request.method == "POST":
        if user_form.is_valid() and doctor_form.is_valid():
            user_form.save()
            doctor_form.save()
            messages.success(request, "Profile updated.")
            return redirect("doctors:dashboard")
        error = first_error(user_form) or first_error(doctor_form)
    return render(request, "edit_profile.html", {
        "forms": [user_form, doctor_form], "error": error,
        "back_url": "doctors:dashboard", "greeting": "Dr. " + request.user.name,
    })
