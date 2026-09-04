from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AvailabilityForm, BookingForm, BookingStatusForm
from .models import Availability, Booking, BookingStatus, ReservationStatus
from .services import create_booking
from payments.domain import create_payout
from payments.models import Transaction

@login_required
def booking_list(request):
    field = 'client' if request.user.role == 'client' else 'photographer'
    bookings = Booking.objects.filter(**{field: request.user}).select_related('client', 'photographer')
    return render(request, 'bookings/list.html', {'bookings': bookings})

@login_required
def booking_create(request):
    if request.user.role != 'client':
        return redirect('booking_list')
    form = BookingForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        service_type = form.cleaned_data['service_type']
        try:
            create_booking(
                client=request.user,
                event_type=service_type.name,
                quoted_price=service_type.suggested_price,
                **form.cleaned_data,
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            return redirect('booking_list')
    return render(request, 'bookings/form.html', {'form': form})


@login_required
def booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk, client=request.user, status=BookingStatus.PENDING)
    form = BookingForm(request.POST or None, instance=booking, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('booking_detail', pk=booking.pk)
    return render(request, 'bookings/form.html', {'form': form, 'booking': booking})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.user not in (booking.client, booking.photographer):
        raise PermissionDenied
    if request.method == 'POST' and booking.status in (
        BookingStatus.PENDING,
        BookingStatus.RESERVATION_DUE,
        BookingStatus.CONFIRMED,
    ):
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
    return redirect('booking_detail', pk=booking.pk)


@login_required
def booking_status_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk, photographer=request.user)
    if request.method == 'POST':
        form = BookingStatusForm(request.POST)
        if form.is_valid():
            next_status = form.cleaned_data['status']
            allowed = {
                BookingStatus.PENDING: {BookingStatus.RESERVATION_DUE, BookingStatus.CANCELLED},
                BookingStatus.ARRIVAL_CONFIRMED: {BookingStatus.BALANCE_DUE},
            }
            if next_status in allowed.get(booking.status, set()):
                booking.status = next_status
                if next_status == BookingStatus.BALANCE_DUE:
                    booking.work_completed_at = timezone.now()
                    booking.save(update_fields=['status', 'work_completed_at', 'updated_at'])
                else:
                    booking.save(update_fields=['status', 'updated_at'])
    return redirect('booking_detail', pk=booking.pk)


@login_required
def availability_manage(request):
    if request.user.role != 'photographer':
        return redirect('booking_list')
    form = AvailabilityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        availability, _ = Availability.objects.update_or_create(
            photographer=request.user,
            date=form.cleaned_data['date'],
            defaults={
                'is_available': form.cleaned_data['is_available'],
                'notes': form.cleaned_data['notes'],
            },
        )
        return redirect('availability_manage')
    availability = Availability.objects.filter(photographer=request.user)
    return render(request, 'bookings/availability.html', {'form': form, 'availability': availability})


@login_required
def availability_toggle(request, pk):
    availability = get_object_or_404(Availability, pk=pk, photographer=request.user)
    if request.method == 'POST':
        availability.is_available = not availability.is_available
        availability.save(update_fields=['is_available'])
    return redirect('availability_manage')


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('client', 'photographer', 'service_type'), pk=pk)
    if request.user != booking.client and request.user != booking.photographer:
        raise PermissionDenied
    return render(request, 'bookings/detail.html', {'booking': booking})


@login_required
def booking_confirm_arrival(request, pk):
    booking = get_object_or_404(Booking, pk=pk, client=request.user)
    if request.method == 'POST' and booking.status == BookingStatus.RESERVED:
        booking.status = BookingStatus.ARRIVAL_CONFIRMED
        booking.reservation_status = ReservationStatus.RELEASED
        booking.arrival_confirmed_at = timezone.now()
        booking.save(update_fields=('status', 'reservation_status', 'arrival_confirmed_at', 'updated_at'))
        reservation_payment = Transaction.objects.filter(
            invoice__booking=booking,
            purpose=Transaction.Purpose.RESERVATION,
            status=Transaction.Status.SUCCESS,
        ).first()
        if reservation_payment:
            create_payout(payment=reservation_payment)
    return redirect('booking_detail', pk=booking.pk)
