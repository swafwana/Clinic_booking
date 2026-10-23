from rest_framework import serializers

from datetime import time
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from .models import Appointment, Availability, Doctor, TimeOff
from .services import get_free_slots
from accounts.models import User


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


class AdminAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ["id", "patient_name", "doctor_name", "date", "time", "reason", "status"]
        read_only_fields = fields

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name() or obj.doctor.user.username}"


class TimeOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeOff
        fields = ["id", "start_date", "end_date", "reason"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})
        return attrs

class DoctorCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    specialty = serializers.CharField(max_length=100)
    bio = serializers.CharField(required=False, allow_blank=True)
    slot_minutes = serializers.IntegerField(min_value=5, max_value=120, default=30)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email", ""),
            role=User.Role.DOCTOR,  # set by the server, never by the browser,  # set by the server, never by the browser
        )
        doctor = Doctor.objects.create(
            user=user,
            specialty=validated_data["specialty"],
            bio=validated_data.get("bio", ""),
            slot_minutes=validated_data["slot_minutes"],
        )
        # Default hours Mon-Fri 09:00-17:00 so the doctor has bookable slots.
        # Change them later in Django admin under Availability.
        Availability.objects.bulk_create([
            Availability(doctor=doctor, weekday=d, start_time=time(9, 0), end_time=time(17, 0))
            for d in range(5)
        ])
        return doctor