from django.db import transaction
from .models import Availability, Booking

def is_date_available(photographer, event_date):
    if Booking.objects.filter(photographer=photographer, event_date=event_date, status__in=['pending', 'confirmed']).exists():
        return False
    return not Availability.objects.filter(photographer=photographer, date=event_date, is_available=False).exists()

@transaction.atomic
def create_booking(*, client, photographer, event_date, **data):
    if not is_date_available(photographer, event_date):
        raise ValueError('This photographer is not available on that date.')
    return Booking.objects.create(client=client, photographer=photographer, event_date=event_date, **data)
