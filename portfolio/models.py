from django.conf import settings
from django.db import models
from django.core.files.base import ContentFile

from .watermarking import branded_copy

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    def __str__(self): return self.name

class Album(models.Model):
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='albums')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='albums')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='portfolio/')
    branded_image = models.ImageField(upload_to='portfolio/branded/', blank=True)
    caption = models.CharField(max_length=255, blank=True)
    watermark_text = models.CharField(max_length=120, blank=True)
    licensing_info = models.CharField(max_length=255, blank=True)
    is_preview = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text='Include this branded photograph in the public gallery.')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_image(self):
        return self.branded_image or self.image

    def save(self, *args, **kwargs):
        create_branded_copy = bool(self.image and (self.is_featured or self.is_preview) and not self.branded_image)
        super().save(*args, **kwargs)
        if create_branded_copy:
            content = branded_copy(self.image)
            self.branded_image.save(f'{self.pk}.jpg', ContentFile(content), save=False)
            super().save(update_fields=['branded_image'])


class DeliveryPhoto(models.Model):
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='delivery_photos')
    image = models.ImageField(upload_to='deliveries/previews/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self._state.adding and self.image:
            content = branded_copy(self.image)
            self.image.save(f'preview-{self.booking_id or "pending"}.jpg', ContentFile(content), save=False)
        super().save(*args, **kwargs)
