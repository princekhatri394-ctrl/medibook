from django.contrib import admin
from django.urls import include, path

from accounts.views import index

admin.site.site_header = "MediBook Admin"
admin.site.site_title = "MediBook Admin"

urlpatterns = [
    path("", index, name="index"),
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("doctor/", include("doctors.urls")),
    path("patient/", include("patients.urls")),
]
