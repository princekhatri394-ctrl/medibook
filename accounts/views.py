from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from doctors.models import Doctor
from patients.models import Patient

from .decorators import redirect_by_role
from .forms import RegisterForm, first_error
from .models import User


def index(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    return redirect("accounts:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    error = ""
    email = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        if not email or not password:
            error = "Please fill in all fields."
        else:
            user = authenticate(request, email=email, password=password)
            if user is None:
                error = "Invalid email or password."
            else:
                login(request, user)
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                    return redirect(next_url)
                return redirect_by_role(user)

    return render(request, "accounts/login.html", {"error": error, "email": email,
                                                   "next": request.GET.get("next", "")})


def register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    error = ""
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    email=data["email"], password=data["password"],
                    name=data["name"].strip(), phone=data["phone"].strip(), role=data["role"],
                )
                if user.role == User.Role.DOCTOR:
                    Doctor.objects.create(
                        user=user,
                        specialization=data.get("specialization") or "",
                        experience=data.get("experience") or 0,
                        fees=data.get("fees") or 0,
                    )
                else:
                    Patient.objects.create(user=user)
            login(request, user)
            if user.role == User.Role.DOCTOR:
                return redirect("doctors:location")
            return redirect("patients:location")
        error = first_error(form)

    return render(request, "accounts/register.html", {"error": error, "values": request.POST})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")
