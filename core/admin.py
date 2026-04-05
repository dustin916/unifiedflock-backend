from django.contrib import admin
from .models import Church, Member, PrayerRequest, Event

admin.site.register(Church)
admin.site.register(Member)
admin.site.register(PrayerRequest)
admin.site.register(Event)