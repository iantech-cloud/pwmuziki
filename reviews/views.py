from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking
from .forms import ReviewForm, ReviewResponseForm
from .models import Review


@login_required
def review_create(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)
    existing = Review.objects.filter(booking=booking).first()
    if existing:
        return redirect('booking_detail', pk=booking.pk)
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.booking = booking
        review.client = request.user
        review.photographer = booking.photographer
        review.save()
        return redirect('booking_detail', pk=booking.pk)
    return render(request, 'reviews/form.html', {'form': form, 'booking': booking})


@login_required
def review_respond(request, review_id):
    review = get_object_or_404(Review.objects.select_related('booking'), pk=review_id, photographer=request.user)
    form = ReviewResponseForm(request.POST or None, instance=review)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('photographer_detail', pk=request.user.pk)
    return render(request, 'reviews/response.html', {'form': form, 'review': review})
