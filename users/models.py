from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        PHOTOGRAPHER = 'photographer', 'Photographer'
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = ['email']

class ClientNote(models.Model):
    class Status(models.TextChoices):
        LEAD = 'lead', 'Lead'
        BOOKED = 'booked', 'Booked'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_notes')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photographer_notes')
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LEAD)
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.CheckConstraint(condition=~models.Q(photographer=models.F('client')), name='note_distinct_users'),
        ]

    def __str__(self):
        return f'{self.client.username} note for {self.photographer.username}'


class GalleryAccess(models.Model):
    album = models.OneToOneField('portfolio.Album', on_delete=models.CASCADE, related_name='client_access')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='galleries')
    password = models.CharField(max_length=128, blank=True)
    allow_downloads = models.BooleanField(default=False)
    allow_favorites = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GalleryFavorite(models.Model):
    gallery = models.ForeignKey(GalleryAccess, on_delete=models.CASCADE, related_name='favorites')
    photo = models.ForeignKey('portfolio.Photo', on_delete=models.CASCADE, related_name='gallery_favorites')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gallery_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['gallery', 'photo', 'client'], name='unique_gallery_favorite')]


class MessageThread(models.Model):
    photographer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_threads')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_threads')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['photographer', 'client'], name='unique_message_thread')]


class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Contract(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        SIGNED = 'signed', 'Signed'

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='contract')
    title = models.CharField(max_length=160, default='Photography agreement')
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudioSettings(models.Model):
    photographer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studio_settings')
    business_name = models.CharField(max_length=160, blank=True)
    service_area = models.CharField(max_length=160, blank=True)
    default_gallery_expiry_days = models.PositiveIntegerField(default=30)
    default_allow_downloads = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    portfolio_link = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True)
    is_featured = models.BooleanField(default=False, help_text='Show this photographer in the featured directory.')

    def __str__(self):
        return f'{self.user.username} profile'

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @classmethod
    def ensure_for(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    Profile.ensure_for(instance)
    instance.profile.save()
