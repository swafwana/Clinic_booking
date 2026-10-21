from datetime import datetime, timedelta

from django.utils import timezone

from .models import Appointment, TimeOff


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