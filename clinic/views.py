from datetime import date, datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole, IsDoctor, IsPatient
from .models import Appointment, Doctor, TimeOff
from .serializers import (
    AdminAppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentSerializer,
    DoctorAppointmentSerializer,
    DoctorSerializer,
    TimeOffSerializer,
)
from .services import get_dashboard_stats, get_free_slots


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DoctorSerializer

    def get_queryset(self):
        qs = Doctor.objects.filter(is_active=True).select_related("user")
        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialty__iexact=specialty)
        return qs.order_by("user__first_name")

    @action(detail=False, methods=["get"])
    def specialties(self, request):
        names = (
            Doctor.objects.filter(is_active=True)
            .order_by("specialty")
            .values_list("specialty", flat=True)
            .distinct()
        )
        return Response(list(names))

    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        doctor = self.get_object()

        raw = request.query_params.get("date")
        if not raw:
            return Response({"detail": "The date parameter is required (YYYY-MM-DD)."}, status=400)
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            return Response({"detail": "Invalid date. Use YYYY-MM-DD."}, status=400)

        free = get_free_slots(doctor, day)
        return Response({
            "doctor": doctor.id,
            "date": raw,
            "slots": [t.strftime("%H:%M") for t in free],
        })


class AppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsPatient]

    def get_queryset(self):
        order = self.request.query_params.get("order", "asc")
        ordering = ("-date", "-time") if order == "desc" else ("date", "time")
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related("doctor__user")
            .order_by(*ordering)
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)


class AppointmentCancelView(APIView):
    permission_classes = [IsPatient]

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.select_related("doctor__user"),
            pk=pk,
            patient=request.user,
        )
        if appointment.status != Appointment.Status.BOOKED:
            return Response(
                {"detail": "Only booked appointments can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        starts_at = timezone.make_aware(
            datetime.combine(appointment.date, appointment.time)
        )
        if starts_at <= timezone.now():
            return Response(
                {"detail": "Past appointments cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


class DoctorAppointmentListView(generics.ListAPIView):
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        order = self.request.query_params.get("order", "asc")
        ordering = ("-date", "-time") if order == "desc" else ("date", "time")
        return (
            Appointment.objects
            .filter(doctor=self.request.user.doctor_profile)
            .select_related("patient")
            .order_by(*ordering)
        )


class DoctorAppointmentStatusView(APIView):
    permission_classes = [IsDoctor]
    new_status = None  # each route in urls.py sets this

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.select_related("patient"),
            pk=pk,
            doctor=request.user.doctor_profile,
        )
        if appointment.status != Appointment.Status.BOOKED:
            return Response(
                {"detail": "Only booked appointments can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = self.new_status
        appointment.save()
        return Response(DoctorAppointmentSerializer(appointment).data)


class DoctorFreeSlotsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        raw = request.query_params.get("date")
        if not raw:
            return Response(
                {"detail": "The date parameter is required (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            return Response(
                {"detail": "Invalid date. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor = request.user.doctor_profile
        free = get_free_slots(doctor, day)
        return Response({
            "doctor": doctor.id,
            "date": raw,
            "slots": [t.strftime("%H:%M") for t in free],
        })


class DoctorTimeOffListCreateView(generics.ListCreateAPIView):
    serializer_class = TimeOffSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return TimeOff.objects.filter(
            doctor=self.request.user.doctor_profile
        ).order_by("-start_date")

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor_profile)


class DoctorTimeOffDeleteView(generics.DestroyAPIView):
    serializer_class = TimeOffSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return TimeOff.objects.filter(
            doctor=self.request.user.doctor_profile
        )


class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(get_dashboard_stats())


class AdminAppointmentListView(generics.ListAPIView):
    serializer_class = AdminAppointmentSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = Appointment.objects.select_related("patient", "doctor__user")
        params = self.request.query_params

        doctor = params.get("doctor")
        if doctor:
            if not doctor.isdigit():
                raise ValidationError({"doctor": "Must be a doctor id number."})
            qs = qs.filter(doctor_id=doctor)

        status_value = params.get("status")
        if status_value:
            if status_value not in Appointment.Status.values:
                raise ValidationError({"status": "Unknown status."})
            qs = qs.filter(status=status_value)

        raw = params.get("date")
        if raw:
            try:
                qs = qs.filter(date=date.fromisoformat(raw))
            except ValueError:
                raise ValidationError({"date": "Invalid date. Use YYYY-MM-DD."})

        order = params.get("order", "asc")
        ordering = ("-date", "-time") if order == "desc" else ("date", "time")
        return qs.order_by(*ordering)
