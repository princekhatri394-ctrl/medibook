from django import forms

from .models import Patient

GENDERS = [("", "-- Select --"), ("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
BLOOD_GROUPS = [("", "-- Select --")] + [(b, b) for b in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]]


class PatientProfileForm(forms.ModelForm):
    gender = forms.ChoiceField(choices=GENDERS, required=False)
    blood_group = forms.ChoiceField(choices=BLOOD_GROUPS, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Patient
        fields = ["date_of_birth", "gender", "blood_group"]
