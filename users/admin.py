from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User


@admin.register(Profile)
class ProfileInlineAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'is_featured', 'phone_number', 'portfolio_link')
    list_filter = ('is_featured',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio')
    autocomplete_fields = ('user',)
    list_editable = ('is_featured',)

    @admin.display(description='Name')
    def display_name(self, obj):
        return obj.display_name


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    max_num = 1
    fields = ('bio', 'portfolio_link', 'phone_number', 'avatar', 'is_featured')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Pwmuziki account', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Pwmuziki account', {'fields': ('email', 'role')}),
    )
    list_display = ('username', 'email', 'full_name', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 30
    inlines = (ProfileInline,)

    @admin.display(description='Name', ordering='first_name')
    def full_name(self, obj):
        return obj.get_full_name() or '—'