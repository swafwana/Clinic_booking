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


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.StringRelatedField(source="doctor")

    class Meta:
        model = Appointment
        fields = ["id", "doctor", "doctor_name", "date", "time", "reason", "status"]
        read_only_fields = fields


class DoctorAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ["id", "patient_name", "date", "time", "reason", "status"]
        read_only_fields = fields

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username