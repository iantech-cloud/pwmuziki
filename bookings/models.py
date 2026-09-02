from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

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
    event_date = models.DateField()
    event_type = models.CharField(max_length=120)
    location = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-event_date']
    def clean(self):
        if self.client_id == self.photographer_id:
            raise ValidationError('A client and photographer must be different users.')
        if self.quoted_price < 0 or self.deposit_amount < 0 or self.deposit_amount > self.quoted_price:
            raise ValidationError('Deposit and quoted price must be valid amounts.')
    @property
    def balance(self): return self.quoted_price - self.deposit_amount
