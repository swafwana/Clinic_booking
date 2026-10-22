from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Doctor
from .serializers import DoctorSerializer,AppointmentCreateSerializer
from .services import get_free_slots
from rest_framework import generics
from accounts.permissions import IsPatient
 

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

class AppointmentCreateView(generics.CreateAPIView):
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsPatient]
    def perform_create(self, serializer):
        serializer.save(patient=self.request.user)