from django import forms

from .models import SPECIALIZATIONS, Doctor


class DoctorProfileForm(forms.ModelForm):
    specialization = forms.ChoiceField(choices=[("", "-- Select Specialization --")] + [(s, s) for s in SPECIALIZATIONS],
                                       required=False)

    class Meta:
        model = Doctor
        fields = ["specialization", "experience", "fees", "bio"]
