from decimal import Decimal
import json
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from bookings.models import Booking, BookingStatus, ReservationStatus
from .models import Invoice, Payout, Transaction
from .domain import create_payout, dispatch_payout
from .services import initiate_stk_push, normalize_phone_number, query_stk_push


def _invoice_for(booking):
    invoice, _ = Invoice.objects.get_or_create(
        booking=booking,
        defaults={
            'number': f'PWM-{booking.pk}-{uuid4().hex[:8].upper()}',
            'total_amount': booking.quoted_price,
            'reservation_amount': booking.reservation_fee,
            'balance_amount': booking.balance,
        },
    )
    if (
        invoice.total_amount != booking.quoted_price
        or invoice.reservation_amount != booking.reservation_fee
        or invoice.balance_amount != booking.balance
    ):
        invoice.total_amount = booking.quoted_price
        invoice.reservation_amount = booking.reservation_fee
        invoice.balance_amount = booking.balance
        invoice.save(update_fields=('total_amount', 'reservation_amount', 'balance_amount'))
    return invoice


@login_required
def payment_start(request, booking_id, phase='reservation'):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)
    if booking.status == BookingStatus.CANCELLED:
        return render(request, 'payments/status.html', {'booking': booking, 'phase': phase, 'error': 'This booking has been cancelled.'})
    if phase == 'reservation':
        amount = booking.reservation_fee
        allowed = booking.status in (BookingStatus.RESERVATION_DUE, BookingStatus.CONFIRMED)
        label = 'reservation fee'
    else:
        amount = booking.balance
        allowed = booking.status == BookingStatus.BALANCE_DUE
        label = 'remaining balance'
    if not allowed or amount <= Decimal('0.00'):
        return render(request, 'payments/status.html', {'booking': booking, 'phase': phase, 'message': 'This payment stage is not currently due.'})
    if request.method != 'POST':
        return render(request, 'payments/form.html', {'booking': booking, 'phase': phase, 'amount': amount, 'label': label})

    phone_number = request.POST.get('phone_number', '').strip()
    if not phone_number:
        return render(request, 'payments/form.html', {'booking': booking, 'phase': phase, 'amount': amount, 'label': label, 'error': 'Enter the M-Pesa phone number to continue.'})
    try:
        normalized_phone = normalize_phone_number(phone_number)
    except ValueError as exc:
        return render(request, 'payments/form.html', {'booking': booking, 'phase': phase, 'amount': amount, 'label': label, 'error': str(exc)})

    invoice = _invoice_for(booking)
    payment = Transaction.objects.create(
        invoice=invoice,
        payer=request.user,
        amount=amount,
        purpose=Transaction.Purpose.RESERVATION if phase == 'reservation' else Transaction.Purpose.BALANCE,
        phone_number=normalized_phone,
    )
    try:
        response = initiate_stk_push(
            phone_number=normalized_phone,
            amount=amount,
            account_reference=f'AUR{booking.pk}{"R" if phase == "reservation" else "B"}'[:12],
            description=f'AuraCity booking {booking.pk}',
        )
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        payment.status = Transaction.Status.FAILED
        payment.result_description = str(exc)
        payment.raw_response = {'error': str(exc)}
        payment.save(update_fields=['status', 'result_description', 'raw_response'])
        return render(request, 'payments/status.html', {'booking': booking, 'phase': phase, 'error': str(exc), 'transaction': payment})

    payment.checkout_request_id = response.get('CheckoutRequestID', '')
    payment.merchant_request_id = response.get('MerchantRequestID', '')
    payment.provider_reference = payment.checkout_request_id or payment.merchant_request_id or None
    payment.raw_response = response
    payment.result_code = str(response.get('ResponseCode', ''))
    payment.result_description = response.get('ResponseDescription', '')
    request_started = str(response.get('ResponseCode', '0')) == '0'
    payment.status = (
        Transaction.Status.INITIATED
        if request_started and payment.checkout_request_id
        else Transaction.Status.FAILED
    )
    if request_started and not payment.checkout_request_id:
        payment.result_description = 'Daraja accepted the request but did not return a checkout ID. Please try again.'
    payment.save(update_fields=[
        'checkout_request_id', 'merchant_request_id', 'provider_reference', 'raw_response',
        'result_code', 'result_description', 'status',
    ])
    if payment.status == Transaction.Status.FAILED:
        return render(request, 'payments/status.html', {'booking': booking, 'phase': phase, 'error': payment.result_description or 'M-Pesa could not start the payment.', 'transaction': payment})
    return render(request, 'payments/status.html', {
        'booking': booking,
        'phase': phase,
        'message': 'Payment request sent. Check your phone to approve it.',
        'transaction': payment,
    })


@login_required
def payment_reservation(request, booking_id):
    return payment_start(request, booking_id, phase='reservation')


@login_required
def payment_balance(request, booking_id):
    return payment_start(request, booking_id, phase='balance')


@login_required
def invoice_detail(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user not in (booking.client, booking.photographer):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    invoice = Invoice.objects.filter(booking=booking).prefetch_related('transactions').first()
    return render(request, 'payments/invoice.html', {'booking': booking, 'invoice': invoice})


@login_required
@require_GET
def payment_status(request, transaction_id):
    payment = get_object_or_404(
        Transaction.objects.select_related('invoice__booking'),
        pk=transaction_id,
        payer=request.user,
    )
    if payment.status == Transaction.Status.INITIATED and payment.checkout_request_id:
        query_key = f'mpesa-status-query:{payment.pk}'
        if cache.add(query_key, True, timeout=8):
            try:
                query_response = query_stk_push(checkout_request_id=payment.checkout_request_id)
            except (RuntimeError, OSError, KeyError, ValueError) as exc:
                query_response = {'query_error': str(exc)}
            else:
                payment.raw_response = {
                    **(payment.raw_response or {}),
                    'last_query': query_response,
                }
                query_result_code = query_response.get('ResultCode')
                if query_result_code not in (None, '', 0, '0'):
                    payment.status = Transaction.Status.FAILED
                    payment.result_code = str(query_result_code)
                    payment.result_description = query_response.get(
                        'ResultDesc',
                        'M-Pesa did not complete the payment.',
                    )
                else:
                    payment.result_description = query_response.get(
                        'ResultDesc',
                        payment.result_description,
                    )
                payment.save(update_fields=[
                    'raw_response', 'status', 'result_code', 'result_description',
                ])
            if query_response.get('query_error'):
                payment.result_description = payment.result_description or query_response['query_error']
        payment.refresh_from_db()
    terminal = payment.status in (Transaction.Status.SUCCESS, Transaction.Status.FAILED)
    return JsonResponse({
        'status': payment.status,
        'status_label': payment.get_status_display(),
        'result_description': payment.result_description,
        'receipt_number': payment.receipt_number,
        'terminal': terminal,
        'success': payment.status == Transaction.Status.SUCCESS,
        'booking_url': f'/bookings/{payment.invoice.booking_id}/',
    })


def _callback_is_authorized(request):
    expected = getattr(settings, 'MPESA_CALLBACK_TOKEN', '')
    if not expected:
        return settings.DEBUG or settings.MPESA_ENVIRONMENT != 'production'
    supplied = request.GET.get('token') or request.headers.get('X-AuraCity-Callback-Token') or request.headers.get('X-Pwmuziki-Callback-Token')
    import hmac
    return bool(supplied) and hmac.compare_digest(supplied, expected)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    if not _callback_is_authorized(request):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Unauthorized callback'}, status=403)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        callback = payload['Body']['stkCallback']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback payload'}, status=400)

    checkout_id = callback.get('CheckoutRequestID')
    payout_payment_id = None
    with transaction.atomic():
        payment = Transaction.objects.select_for_update().select_related('invoice', 'invoice__booking').filter(
            checkout_request_id=checkout_id,
        ).first()
        if not payment:
            payment = Transaction.objects.select_for_update().select_related('invoice', 'invoice__booking').filter(
                provider_reference=checkout_id,
            ).first()
        if not payment:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback acknowledged'})
        if payment.status == Transaction.Status.SUCCESS:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback already processed'})

        payment.raw_response = payload
        payment.callback_received_at = timezone.now()
        payment.result_code = str(callback.get('ResultCode', ''))
        payment.result_description = callback.get('ResultDesc', '')
        metadata = {
            item.get('Name'): item.get('Value')
            for item in callback.get('CallbackMetadata', {}).get('Item', [])
            if item.get('Name')
        }
        try:
            callback_amount = Decimal(str(metadata['Amount']))
        except (KeyError, TypeError, ValueError):
            callback_amount = None
        receipt_number = str(metadata.get('MpesaReceiptNumber') or '')
        amount_matches = callback_amount is not None and callback_amount == payment.amount
        successful = str(callback.get('ResultCode')) == '0'
        if successful and amount_matches and receipt_number:
            payment.status = Transaction.Status.SUCCESS
            payment.receipt_number = receipt_number
            invoice = payment.invoice
            if payment.purpose == Transaction.Purpose.RESERVATION:
                invoice.reservation_paid = True
                invoice.reservation_amount = payment.amount
                invoice.save(update_fields=['reservation_paid', 'reservation_amount'])
                booking = invoice.booking
                booking.reservation_status = ReservationStatus.HELD
                booking.reservation_paid_at = timezone.now()
                if booking.status in (BookingStatus.RESERVATION_DUE, BookingStatus.CONFIRMED):
                    booking.status = BookingStatus.RESERVED
                booking.save(update_fields=('reservation_status', 'reservation_paid_at', 'status', 'updated_at'))
            else:
                invoice.balance_paid = True
                invoice.is_paid = True
                invoice.balance_amount = payment.amount
                invoice.save(update_fields=['balance_paid', 'is_paid', 'balance_amount'])
                booking = invoice.booking
                booking.balance_paid_at = timezone.now()
                booking.status = BookingStatus.COMPLETED
                booking.save(update_fields=('balance_paid_at', 'status', 'updated_at'))
                payout_payment_id = payment.pk
        else:
            payment.status = Transaction.Status.FAILED
            if successful:
                payment.result_description = 'Callback amount or receipt did not match the initiated transaction.'
                payment.raw_response = {**payload, 'validation_error': payment.result_description}
        payment.save(update_fields=[
            'status', 'raw_response', 'receipt_number', 'result_code',
            'result_description', 'callback_received_at',
        ])
    if payout_payment_id:
        try:
            dispatch_payout(payout=create_payout(payment=Transaction.objects.get(pk=payout_payment_id)))
        except (RuntimeError, OSError, ValueError):
            # The payment remains successful; payout status records the operational failure.
            pass
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback processed'})


@csrf_exempt
@require_POST
def mpesa_b2c_result(request):
    if not _callback_is_authorized(request):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Unauthorized callback'}, status=403)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        result = payload['Result']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid B2C result payload'}, status=400)
    references = [
        result.get('ConversationID'),
        result.get('OriginatorConversationID'),
        result.get('TransactionID'),
    ]
    with transaction.atomic():
        payout = Payout.objects.select_for_update().filter(
            provider_reference__in=[ref for ref in references if ref],
        ).first()
        if not payout:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Result acknowledged'})
        if payout.status == Payout.Status.PAID:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Result already processed'})
        payout.raw_response = payload
        result_amount = result.get('ResultParameters', {}).get('ResultParameter', [])
        amount_item = next(
            (item for item in result_amount if item.get('Key') in ('TransactionAmount', 'Amount')),
            None,
        )
        try:
            callback_amount = Decimal(str(amount_item.get('Value'))) if amount_item else None
        except (TypeError, ValueError):
            callback_amount = None
        amount_mismatch = amount_item is not None and callback_amount != payout.amount
        if str(result.get('ResultCode')) == '0' and amount_mismatch:
            payout.status = Payout.Status.FAILED
            payout.failure_reason = 'Daraja returned a payout amount that did not match the requested amount.'
        elif str(result.get('ResultCode')) == '0':
            payout.status = Payout.Status.PAID
            payout.paid_at = timezone.now()
            payout.failure_reason = ''
        else:
            payout.status = Payout.Status.FAILED
            payout.failure_reason = result.get('ResultDesc', 'Daraja payout failed.')
        payout.save(update_fields=['status', 'paid_at', 'failure_reason', 'raw_response'])
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Result processed'})


@csrf_exempt
@require_POST
def mpesa_b2c_timeout(request):
    if not _callback_is_authorized(request):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Unauthorized callback'}, status=403)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        result = payload.get('Result', {})
    except (ValueError, TypeError):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid B2C timeout payload'}, status=400)
    references = [
        result.get('ConversationID'),
        result.get('OriginatorConversationID'),
    ]
    payout = Payout.objects.filter(provider_reference__in=[ref for ref in references if ref]).first()
    if payout and payout.status != Payout.Status.PAID:
        payout.status = Payout.Status.FAILED
        payout.failure_reason = result.get('ResultDesc', 'Daraja payout timed out.')
        payout.raw_response = payload
        payout.save(update_fields=['status', 'failure_reason', 'raw_response'])
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Timeout acknowledged'})
