from django.conf import settings
from django.db import models

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
    caption = models.CharField(max_length=255, blank=True)
    watermark_text = models.CharField(max_length=120, blank=True)
    licensing_info = models.CharField(max_length=255, blank=True)
    is_preview = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
