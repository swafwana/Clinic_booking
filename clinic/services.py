from datetime import datetime, timedelta

from django.utils import timezone

from .models import Appointment, TimeOff,Doctor

from django.db.models import Count, Q



def get_free_slots(doctor, day):
    """Return a list of free start times (datetime.time) for a doctor on a date."""
    now = timezone.localtime()

    # Past days have no bookable slots.
    if day < now.date():
        return []

    # Step 2: doctor on time off that day?
    if TimeOff.objects.filter(doctor=doctor, start_date__lte=day, end_date__gte=day).exists():
        return []

    # Step 3: weekly working hours for that weekday (0 = Monday).
    windows = doctor.availabilities.filter(weekday=day.weekday()).order_by("start_time")

    # Times already taken by booked appointments.
    booked = set(
        Appointment.objects.filter(
            doctor=doctor, date=day, status=Appointment.Status.BOOKED
        ).values_list("time", flat=True)
    )

    # Step 4 and 5: cut hours into slots, skip booked ones and times already passed today.
    step = timedelta(minutes=doctor.slot_minutes)
    free = []
    for window in windows:
        current = datetime.combine(day, window.start_time)
        end = datetime.combine(day, window.end_time)
        while current + step <= end:
            t = current.time()
            already_passed = day == now.date() and t <= now.time()
            if t not in booked and not already_passed:
                free.append(t)
            current += step
    return free

def get_dashboard_stats():
    today = timezone.localdate()

    # Count per status. Start every status at 0 so none is missing.
    by_status = {value: 0 for value, _label in Appointment.Status.choices}
    for row in Appointment.objects.values("status").annotate(n=Count("id")):
        by_status[row["status"]] = row["n"]

    # One query that counts per doctor id.
    rows = Appointment.objects.values("doctor_id").annotate(
        total=Count("id"),
        booked=Count("id", filter=Q(status=Appointment.Status.BOOKED)),
    )
    counts = {r["doctor_id"]: r for r in rows}

    per_doctor = []
    doctors = Doctor.objects.filter(is_active=True).select_related("user")
    for d in doctors.order_by("user__first_name"):
        c = counts.get(d.id, {"total": 0, "booked": 0})
        per_doctor.append({
            "doctor": f"Dr. {d.user.get_full_name() or d.user.username}",
            "specialty": d.specialty,
            "total": c["total"],
            "booked": c["booked"],
        })

    return {
        "total": Appointment.objects.count(),
        "today": Appointment.objects.filter(date=today).count(),
        "by_status": by_status,
        "per_doctor": per_doctor,
    }