from django.contrib import admin

from .models import Invoice, Payout, Refund, Transaction


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('provider', 'provider_reference', 'amount', 'purpose', 'status', 'raw_response', 'created_at')
    can_delete = False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'booking', 'client', 'photographer', 'total_amount', 'reservation_paid', 'balance_paid', 'is_paid', 'due_date', 'issued_at')
    list_filter = ('reservation_paid', 'balance_paid', 'is_paid', 'due_date', 'issued_at')
    search_fields = ('number', 'booking__event_type', 'booking__client__username', 'booking__photographer__username')
    autocomplete_fields = ('booking',)
    readonly_fields = ('number', 'issued_at')
    inlines = (TransactionInline,)

    @admin.display(description='Client')
    def client(self, obj):
        return obj.booking.client

    @admin.display(description='Photographer')
    def photographer(self, obj):
        return obj.booking.photographer


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'payer', 'provider', 'purpose', 'amount', 'status', 'provider_reference', 'created_at')
    list_filter = ('provider', 'purpose', 'status', 'created_at')
    search_fields = ('provider_reference', 'payer__username', 'payer__email', 'invoice__number')
    autocomplete_fields = ('invoice', 'payer')
    readonly_fields = ('created_at', 'raw_response')
    fieldsets = (
        ('Payment', {'fields': ('invoice', 'payer', 'provider', 'purpose', 'amount', 'status')}),
        ('Daraja response', {'fields': ('provider_reference', 'raw_response'), 'classes': ('collapse',)}),
        ('Audit', {'fields': ('created_at',)}),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'amount', 'status', 'provider_reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction__provider_reference', 'reason', 'provider_reference')
    autocomplete_fields = ('transaction',)
    readonly_fields = ('created_at',)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'photographer', 'transaction', 'amount', 'status', 'provider_reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('photographer__username', 'photographer__email', 'transaction__provider_reference', 'provider_reference')
    autocomplete_fields = ('photographer', 'transaction')
    readonly_fields = ('created_at',)