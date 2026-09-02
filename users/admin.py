from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Pwmuziki', {'fields': ('role',)}),)
    list_display = ('username', 'email', 'role', 'is_active')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'portfolio_link')
