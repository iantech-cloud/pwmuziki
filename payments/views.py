from decimal import Decimal
import json
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bookings.models import Booking, BookingStatus
from .models import Invoice, Transaction
from .services import initiate_stk_push


def _invoice_for(booking):
    invoice, _ = Invoice.objects.get_or_create(
        booking=booking,
        defaults={
            'number': f'PWM-{booking.pk}-{uuid4().hex[:8].upper()}',
            'total_amount': booking.balance,
        },
    )
    return invoice


@login_required
def payment_start(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)
    if booking.status == BookingStatus.CANCELLED:
        return render(request, 'payments/status.html', {'booking': booking, 'error': 'This booking has been cancelled.'})
    if booking.balance <= Decimal('0.00'):
        return render(request, 'payments/status.html', {'booking': booking, 'message': 'This booking is already fully paid.'})
    if request.method != 'POST':
        return render(request, 'payments/form.html', {'booking': booking})

    phone_number = request.POST.get('phone_number', '').strip()
    if not phone_number:
        return render(request, 'payments/form.html', {'booking': booking, 'error': 'Enter the M-Pesa phone number to continue.'})

    invoice = _invoice_for(booking)
    transaction = Transaction.objects.create(
        invoice=invoice,
        payer=request.user,
        amount=booking.balance,
    )
    try:
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=booking.balance,
            account_reference=invoice.number,
            description=f'Pwmuziki booking {booking.pk}',
        )
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        transaction.status = Transaction.Status.FAILED
        transaction.raw_response = {'error': str(exc)}
        transaction.save(update_fields=['status', 'raw_response'])
        return render(request, 'payments/status.html', {'booking': booking, 'error': str(exc)})

    transaction.provider_reference = response.get('CheckoutRequestID') or response.get('MerchantRequestID')
    transaction.raw_response = response
    transaction.status = (
        Transaction.Status.INITIATED
        if str(response.get('ResponseCode', '0')) == '0'
        else Transaction.Status.FAILED
    )
    transaction.save(update_fields=['provider_reference', 'raw_response', 'status'])
    if transaction.status == Transaction.Status.FAILED:
        return render(request, 'payments/status.html', {'booking': booking, 'error': response.get('ResponseDescription', 'M-Pesa could not start the payment.')})
    return render(request, 'payments/status.html', {'booking': booking, 'message': 'Payment request sent. Check your phone to approve it.'})


@login_required
def invoice_detail(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user not in (booking.client, booking.photographer):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    invoice = Invoice.objects.filter(booking=booking).prefetch_related('transactions').first()
    return render(request, 'payments/invoice.html', {'booking': booking, 'invoice': invoice})


@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
        callback = payload['Body']['stkCallback']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback payload'}, status=400)

    checkout_id = callback.get('CheckoutRequestID')
    transaction = Transaction.objects.filter(provider_reference=checkout_id).select_related('invoice').first()
    if not transaction:
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback acknowledged'})

    transaction.raw_response = payload
    if str(callback.get('ResultCode')) == '0':
        transaction.status = Transaction.Status.SUCCESS
        transaction.invoice.is_paid = True
        transaction.invoice.save(update_fields=['is_paid'])
    else:
        transaction.status = Transaction.Status.FAILED
    transaction.save(update_fields=['status', 'raw_response'])
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback processed'})
