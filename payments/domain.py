from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Payout, Refund, Transaction
from .services import initiate_b2c_payout


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
    payout, _ = Payout.objects.get_or_create(
        transaction=payment,
        defaults={
            'photographer': payment.invoice.booking.photographer,
            'amount': payment.amount,
        },
    )
    return payout


@transaction.atomic
def dispatch_payout(*, payout):
    if payout.status == Payout.Status.PAID:
        return payout
    booking = payout.transaction.invoice.booking
    if payout.transaction.purpose == Transaction.Purpose.RESERVATION and booking.reservation_status != 'released':
        raise ValueError('Reservation escrow can only be paid after client arrival confirmation.')
    phone_number = getattr(getattr(payout.photographer, 'profile', None), 'phone_number', '')
    if not phone_number:
        raise ValueError('The photographer must add a payout phone number to their profile.')
    try:
        response = initiate_b2c_payout(
            phone_number=phone_number,
            amount=payout.amount,
            remarks=f'Pwmuziki payout for booking {booking.pk}',
            occasion=payout.transaction.purpose,
        )
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        payout.status = Payout.Status.FAILED
        payout.failure_reason = str(exc)
        payout.requested_at = timezone.now()
        payout.save(update_fields=['status', 'failure_reason', 'requested_at'])
        return payout
    payout.status = Payout.Status.PROCESSING
    payout.provider_reference = (
        response.get('ConversationID')
        or response.get('OriginatorConversationID')
        or response.get('TransactionID')
        or ''
    )
    payout.failure_reason = ''
    payout.requested_at = timezone.now()
    payout.save(update_fields=['status', 'provider_reference', 'failure_reason', 'requested_at'])
    return payout