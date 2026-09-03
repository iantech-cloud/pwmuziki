from decimal import Decimal

from django.db import transaction

from .models import Payout, Refund, Transaction


@transaction.atomic
def request_refund(*, payment, amount=None, reason=''):
    if payment.status != Transaction.Status.SUCCESS:
        raise ValueError('Only successful payments can be refunded.')
    amount = amount if amount is not None else payment.amount
    already_refunded = sum(
        (refund.amount for refund in payment.refunds.exclude(status=Refund.Status.REJECTED)),
        Decimal('0.00'),
    )
    if amount <= 0 or already_refunded + amount > payment.amount:
        raise ValueError('The requested refund is greater than the remaining refundable amount.')
    return Refund.objects.create(transaction=payment, amount=amount, reason=reason)


@transaction.atomic
def create_payout(*, payment):
    if payment.status != Transaction.Status.SUCCESS:
        raise ValueError('A payout can only be created from a successful payment.')
    return Payout.objects.get_or_create(
        transaction=payment,
        defaults={
            'photographer': payment.invoice.booking.photographer,
            'amount': payment.amount,
        },
    )[0]