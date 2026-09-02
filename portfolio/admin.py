from django.contrib import admin
from .models import Album, Category, Photo
admin.site.register(Category)
admin.site.register(Album)
admin.site.register(Photo)
