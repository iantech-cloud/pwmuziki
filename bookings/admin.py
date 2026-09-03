from django.contrib import admin, messages

from .models import Availability, Booking, BookingStatus


@admin.action(description='Confirm selected bookings')
def confirm_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status=BookingStatus.PENDING)
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.CONFIRMED
        booking.save(update_fields=('status', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) confirmed.', messages.SUCCESS)


@admin.action(description='Mark selected bookings completed')
def complete_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status=BookingStatus.CONFIRMED)
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.COMPLETED
        booking.save(update_fields=('status', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) completed.', messages.SUCCESS)


@admin.action(description='Cancel selected bookings')
def cancel_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED])
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=('status', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) cancelled.', messages.WARNING)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'event_type', 'event_date', 'client', 'photographer', 'status', 'quoted_price', 'created_at')
    list_filter = ('status', 'event_date', 'created_at')
    search_fields = ('event_type', 'location', 'details', 'client__username', 'client__email', 'photographer__username', 'photographer__email')
    autocomplete_fields = ('client', 'photographer')
    readonly_fields = ('created_at', 'updated_at', 'balance')
    date_hierarchy = 'event_date'
    list_per_page = 30
    actions = (confirm_bookings, complete_bookings, cancel_bookings)
    fieldsets = (
        ('People', {'fields': ('client', 'photographer')}),
        ('Event', {'fields': ('event_type', 'event_date', 'location', 'details')}),
        ('Commercial', {'fields': ('quoted_price', 'deposit_amount', 'balance', 'status')}),
        ('Audit', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Reference', ordering='pk')
    def reference(self, obj):
        return f'BK-{obj.pk:05d}'


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('photographer', 'date', 'is_available', 'notes')
    list_filter = ('is_available', 'date')
    search_fields = ('photographer__username', 'photographer__email', 'notes')
    autocomplete_fields = ('photographer',)
    date_hierarchy = 'date'