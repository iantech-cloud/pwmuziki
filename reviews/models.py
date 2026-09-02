from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from bookings.models import Booking

class Rating(models.Model):
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    def __str__(self): return f'{self.value}/5'

class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_written')
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField()
    photographer_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def clean(self):
        if self.booking.client_id != self.client_id or self.booking.photographer_id != self.photographer_id:
            from django.core.exceptions import ValidationError
            raise ValidationError('Review participants must match the booking.')
