from django.contrib import admin
from .models import Doctor, Availability, TimeOff, Appointment

admin.site.register(Doctor)
admin.site.register(Availability)
admin.site.register(TimeOff)
admin.site.register(Appointment)