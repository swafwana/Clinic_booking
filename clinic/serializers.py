from rest_framework import serializers

from .models import Appointment, Doctor
from .services import get_free_slots

class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ["id", "name", "specialty", "bio", "slot_minutes"]

    def get_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"

class AppointmentCreateSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_active=True)
    )

    class Meta:
        model = Appointment
        fields = ["id", "doctor", "date", "time", "reason", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        if attrs["time"] not in get_free_slots(attrs["doctor"], attrs["date"]):
            raise serializers.ValidationError("That slot is not available.")
        return attrs