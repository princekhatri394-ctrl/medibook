from django import forms
from django.contrib.auth import password_validation

from doctors.models import SPECIALIZATIONS

from .models import User


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=150)
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[(User.Role.PATIENT, "Patient"), (User.Role.DOCTOR, "Doctor")])
    specialization = forms.ChoiceField(choices=[("", "")] + [(s, s) for s in SPECIALIZATIONS], required=False)
    experience = forms.IntegerField(min_value=0, max_value=60, required=False)
    fees = forms.DecimalField(min_value=0, max_digits=8, decimal_places=2, required=False)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please login.")
        return email

    def clean(self):
        data = super().clean()
        password, confirm = data.get("password"), data.get("confirm_password")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        if password:
            password_validation.validate_password(
                password, User(email=data.get("email", ""), name=data.get("name", ""))
            )
        return data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "phone"]


def first_error(form):
    for errors in form.errors.values():
        return errors[0]
    return ""
