from django.contrib import admin
from .models import Availability, Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'event_date', 'client', 'photographer', 'status', 'quoted_price')
    list_filter = ('status', 'event_date')
    search_fields = ('event_type', 'location', 'client__username', 'photographer__username')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('photographer', 'date', 'is_available')
    list_filter = ('is_available', 'date')
