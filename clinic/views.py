from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Doctor,Appointment
from .serializers import DoctorSerializer,AppointmentCreateSerializer,AppointmentSerializer
from .services import get_free_slots
from rest_framework import generics
from accounts.permissions import IsPatient
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime

from django.utils import timezone
 

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
        return Appointment.objects.filter(
            patient=self.request.user
        ).select_related("doctor__user")

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