from rest_framework import serializers

from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ["id", "name", "specialty", "bio", "slot_minutes"]

    def get_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"