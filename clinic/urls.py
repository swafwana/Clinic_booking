from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppointmentCancelView, AppointmentListCreateView, DoctorViewSet

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = [
    path("", include(router.urls)),
    path("appointments/", AppointmentListCreateView.as_view()),
    path("appointments/<int:pk>/cancel/", AppointmentCancelView.as_view()),
]