from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from .forms import BookingForm
from .models import Booking
from .services import create_booking

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
        try:
            create_booking(client=request.user, **form.cleaned_data)
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            return redirect('booking_list')
    return render(request, 'bookings/form.html', {'form': form})

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('client', 'photographer'), pk=pk)
    if request.user != booking.client and request.user != booking.photographer:
        raise PermissionDenied
    return render(request, 'bookings/detail.html', {'booking': booking})
