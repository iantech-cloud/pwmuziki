from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ServiceType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RESERVATION_DUE = 'reservation_due', 'Reservation fee due'
    RESERVED = 'reserved', 'Reserved'
    ARRIVAL_CONFIRMED = 'arrival_confirmed', 'Arrival confirmed'
    BALANCE_DUE = 'balance_due', 'Balance due'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    CONFIRMED = 'confirmed', 'Confirmed (legacy)'


class ReservationStatus(models.TextChoices):
    DUE = 'due', 'Reservation fee due'
    HELD = 'held', 'Held in escrow'
    RELEASED = 'released', 'Released to photographer'
    REFUNDED = 'refunded', 'Refunded'

class Availability(models.Model):
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    class Meta:
        unique_together = ('photographer', 'date')
        ordering = ['date']

class Booking(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_bookings')
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='photographer_bookings')
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    event_date = models.DateField()
    event_type = models.CharField(max_length=120)
    location = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reservation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    reservation_status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.DUE)
    reservation_paid_at = models.DateTimeField(null=True, blank=True)
    arrival_confirmed_at = models.DateTimeField(null=True, blank=True)
    work_completed_at = models.DateTimeField(null=True, blank=True)
    balance_paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-event_date']
    def clean(self):
        if self.client_id == self.photographer_id:
            raise ValidationError('A client and photographer must be different users.')
        if self.quoted_price < 0:
            raise ValidationError('Quoted price must be a valid amount.')

    def save(self, *args, **kwargs):
        self.reservation_fee = (self.quoted_price * Decimal('0.20')).quantize(Decimal('0.01'))
        self.deposit_amount = self.reservation_fee
        super().save(*args, **kwargs)

    @property
    def balance(self): return self.quoted_price - self.reservation_fee

    @property
    def reservation_percentage(self):
        return Decimal('20')
