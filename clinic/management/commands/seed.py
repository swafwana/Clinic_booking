from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from clinic.models import Appointment, Availability, Doctor, TimeOff

PASSWORD = "demo1234"

# username, first, last, specialty, bio, weekdays (0=Mon), start, end
DOCTORS = [
    ("dr_nair", "Meera", "Nair", "Dermatology", "Skin, hair and allergy care.", [0, 1, 2, 3], "09:00", "13:00"),
    ("dr_sharma", "Arjun", "Sharma", "Cardiology", "Heart health and prevention.", [0, 1, 2, 3, 4], "10:00", "14:00"),
    ("dr_iyer", "Rohan", "Iyer", "General Medicine", "Everyday illness and checkups.", [0, 1, 2, 3, 4], "09:00", "13:00"),
    ("dr_verma", "Anita", "Verma", "Pediatrics", "Care for infants and children.", [1, 2, 3, 4, 5], "09:00", "12:00"),
]

PATIENTS = [
    ("sara", "Sara", "Khan", "9876500001"),
    ("rahul", "Rahul", "Mehta", "9876500002"),
    ("priya", "Priya", "Das", "9876500003"),
]


def parse(t):
    return datetime.strptime(t, "%H:%M").time()


def slot_time(start, minutes, index):
    base = datetime.combine(datetime(2000, 1, 1), start)
    return (base + timedelta(minutes=minutes * index)).time()


def working_dates(weekdays, start, step, count):
    """Next (step=1) or previous (step=-1) `count` dates falling on a working weekday."""
    found, d = [], start
    while len(found) < count:
        if d.weekday() in weekdays:
            found.append(d)
        d += timedelta(days=step)
    return found


class Command(BaseCommand):
    help = "Create demo doctors, patients, availability, time off and appointments."

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()

        User.objects.filter(is_superuser=True).update(role=User.Role.ADMIN, is_staff=True)

        patients = []
        for username, first, last, phone in PATIENTS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "phone": phone,
                          "email": f"{username}@example.com", "role": User.Role.PATIENT},
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            patients.append(user)

        doctors = []
        for username, first, last, specialty, bio, days, start, end in DOCTORS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last,
                          "email": f"{username}@example.com", "role": User.Role.DOCTOR},
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            doctor, _ = Doctor.objects.get_or_create(
                user=user, defaults={"specialty": specialty, "bio": bio, "slot_minutes": 30})
            for weekday in days:
                Availability.objects.get_or_create(
                    doctor=doctor, weekday=weekday,
                    defaults={"start_time": parse(start), "end_time": parse(end)})
            doctors.append((doctor, set(days), parse(start)))

        first_doctor = doctors[0][0]
        TimeOff.objects.get_or_create(
            doctor=first_doctor,
            start_date=today + timedelta(days=7),
            end_date=today + timedelta(days=8),
            defaults={"reason": "Medical conference"})

        for i, (doctor, days, start) in enumerate(doctors):
            minutes = doctor.slot_minutes
            upcoming = working_dates(days, today + timedelta(days=1), 1, 2)
            past = working_dates(days, today - timedelta(days=1), -1, 2)

            plan = [
                (upcoming[0], 0, patients[i % 3], Appointment.Status.BOOKED, "Routine consultation"),
                (upcoming[0], 2, patients[(i + 1) % 3], Appointment.Status.BOOKED, "Follow-up visit"),
                (upcoming[1], 1, patients[(i + 2) % 3], Appointment.Status.BOOKED, "First visit"),
                (past[0], 0, patients[i % 3], Appointment.Status.COMPLETED, "Checkup"),
                (past[0], 1, patients[(i + 1) % 3], Appointment.Status.NO_SHOW, "Consultation"),
                (past[1], 0, patients[(i + 2) % 3], Appointment.Status.CANCELLED, "Consultation"),
            ]
            for day, index, patient, status, reason in plan:
                Appointment.objects.get_or_create(
                    doctor=doctor, date=day, time=slot_time(start, minutes, index),
                    defaults={"patient": patient, "status": status, "reason": reason})

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(f"Doctors: {', '.join(d[0].user.username for d in doctors)}")
        self.stdout.write(f"Patients: {', '.join(p.username for p in patients)}")
        self.stdout.write(f"Password for all demo users: {PASSWORD}")
        self.stdout.write("Admin: your superuser account (role set to admin).")