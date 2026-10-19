from django.conf import settings
from django.db import models
from django.db.models import Q


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile")
    specialty = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    slot_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.specialty})"


class Availability(models.Model):
    """Weekly recurring working hours, e.g. Monday 09:00-13:00."""
    WEEKDAYS = [(0, "Mon"), (1, "Tue"), (2, "Wed"), (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun")]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="availabilities")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)   # matches date.weekday()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.doctor} {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class TimeOff(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="time_off")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.doctor} off {self.start_date} to {self.end_date}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked"
        CANCELLED = "cancelled"
        COMPLETED = "completed"
        NO_SHOW = "no_show"

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BOOKED)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time"],
                condition=Q(status="booked"),
                name="unique_booked_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.date} {self.time}"