"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("clinic.urls")),
    path("api/auth/", include("accounts.urls")),
    path("login/", TemplateView.as_view(template_name="accounts/login.html")),
    path("doctors/", TemplateView.as_view(template_name="clinic/doctors.html")),
    path("doctors/<int:doctor_id>/book/", TemplateView.as_view(template_name="clinic/book.html")),
    path("appointments/", TemplateView.as_view(template_name="clinic/my_appointments.html")),
    path("doctor/schedule/", TemplateView.as_view(template_name="clinic/doctor_schedule.html")),
    path("dashboard/", TemplateView.as_view(template_name="clinic/dashboard.html")),
]
