from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentCancelView, 
    AppointmentListCreateView,
     DoctorViewSet,
     DoctorAppointmentListView,
     DoctorAppointmentStatusView,
     DoctorFreeSlotsView,
     AdminStatsView,
     AdminAppointmentListView)
from .models import Appointment
router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = [
    path("", include(router.urls)),
    path("appointments/", AppointmentListCreateView.as_view()),
    path("appointments/<int:pk>/cancel/", AppointmentCancelView.as_view()),
    path("doctor/appointments/", DoctorAppointmentListView.as_view()),
        path(
        "doctor/appointments/<int:pk>/complete/",
        DoctorAppointmentStatusView.as_view(new_status=Appointment.Status.COMPLETED),
    ),
    path(
        "doctor/appointments/<int:pk>/no-show/",
        DoctorAppointmentStatusView.as_view(new_status=Appointment.Status.NO_SHOW),
    ),
    path("doctor/slots/", DoctorFreeSlotsView.as_view()),
    path("dashboard/stats/", AdminStatsView.as_view()),
    path("dashboard/appointments/", AdminAppointmentListView.as_view()),
]