from django.contrib import admin, messages
from django.utils import timezone

from .models import Availability, Booking, BookingStatus, ServiceType


@admin.action(description='Confirm selected bookings')
def confirm_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status=BookingStatus.PENDING)
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.RESERVATION_DUE
        booking.save(update_fields=('status', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) confirmed.', messages.SUCCESS)


@admin.action(description='Mark selected bookings ready for final payment')
def complete_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status=BookingStatus.ARRIVAL_CONFIRMED)
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.BALANCE_DUE
        booking.work_completed_at = timezone.now()
        booking.save(update_fields=('status', 'work_completed_at', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) completed.', messages.SUCCESS)


@admin.action(description='Cancel selected bookings')
def cancel_bookings(modeladmin, request, queryset):
    selected = queryset.filter(status__in=[
        BookingStatus.PENDING,
        BookingStatus.RESERVATION_DUE,
        BookingStatus.RESERVED,
    ])
    updated = 0
    for booking in selected:
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=('status', 'updated_at'))
        updated += 1
    modeladmin.message_user(request, f'{updated} booking(s) cancelled.', messages.WARNING)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'event_type', 'event_date', 'client', 'photographer', 'status', 'reservation_status', 'quoted_price', 'created_at')
    list_filter = ('status', 'reservation_status', 'service_type', 'event_date', 'created_at')
    search_fields = ('event_type', 'location', 'details', 'client__username', 'client__email', 'photographer__username', 'photographer__email')
    autocomplete_fields = ('client', 'photographer', 'service_type')
    readonly_fields = ('created_at', 'updated_at', 'balance', 'reservation_fee', 'reservation_paid_at', 'arrival_confirmed_at', 'work_completed_at', 'balance_paid_at')
    date_hierarchy = 'event_date'
    list_per_page = 30
    actions = (confirm_bookings, complete_bookings, cancel_bookings)
    fieldsets = (
        ('People', {'fields': ('client', 'photographer')}),
        ('Event', {'fields': ('service_type', 'event_type', 'event_date', 'location', 'details')}),
        ('Commercial', {'fields': ('quoted_price', 'reservation_fee', 'deposit_amount', 'balance', 'status', 'reservation_status')}),
        ('Milestones', {'fields': ('reservation_paid_at', 'arrival_confirmed_at', 'work_completed_at', 'balance_paid_at'), 'classes': ('collapse',)}),
        ('Audit', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Reference', ordering='pk')
    def reference(self, obj):
        return f'BK-{obj.pk:05d}'


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'suggested_price', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('photographer', 'date', 'is_available', 'notes')
    list_filter = ('is_available', 'date')
    search_fields = ('photographer__username', 'photographer__email', 'notes')
    autocomplete_fields = ('photographer',)
    date_hierarchy = 'date'