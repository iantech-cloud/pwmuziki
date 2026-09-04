from django.conf import settings
from django.db import models
from bookings.models import Booking

class Invoice(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    number = models.CharField(max_length=40, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reservation_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reservation_paid = models.BooleanField(default=False)
    balance_paid = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    issued_at = models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
    class Purpose(models.TextChoices):
        RESERVATION = 'reservation', 'Reservation fee'
        BALANCE = 'balance', 'Final balance'
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='transactions')
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    provider = models.CharField(max_length=30, default='mpesa')
    provider_reference = models.CharField(max_length=120, blank=True, unique=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.RESERVATION)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(Transaction):
    class Meta:
        proxy = True


class Refund(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Requested'
        APPROVED = 'approved', 'Approved'
        PROCESSED = 'processed', 'Processed'
        REJECTED = 'rejected', 'Rejected'

    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    provider_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount <= 0 or self.amount > self.transaction.amount:
            raise ValidationError('Refund amount must be positive and no greater than the transaction.')


class Payout(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='payout')
    photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
