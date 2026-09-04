from django.db import transaction
from django.utils import timezone
from .models import Availability, Booking

def is_date_available(photographer, event_date):
    active_statuses = [
        'pending', 'reservation_due', 'reserved', 'arrival_confirmed', 'balance_due', 'confirmed',
    ]
    if Booking.objects.filter(photographer=photographer, event_date=event_date, status__in=active_statuses).exists():
        return False
    return not Availability.objects.filter(photographer=photographer, date=event_date, is_available=False).exists()

@transaction.atomic
def create_booking(*, client, photographer, event_date, **data):
    if client.role != 'client' or photographer.role != 'photographer':
        raise ValueError('Bookings must connect a client with a photographer.')
    if event_date < timezone.localdate():
        raise ValueError('Choose a date in the future.')
    if not is_date_available(photographer, event_date):
        raise ValueError('This photographer is not available on that date.')
    return Booking.objects.create(client=client, photographer=photographer, event_date=event_date, **data)
