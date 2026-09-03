from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        PHOTOGRAPHER = 'photographer', 'Photographer'
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = ['email']

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
