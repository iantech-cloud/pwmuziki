from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from users.models import User
from .models import Availability, Booking, BookingStatus, ServiceType

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('photographer', 'service_type', 'photo_count', 'event_date', 'location', 'details')
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Share the mood, timing, and anything else that matters...'}),
        }
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['photographer'].queryset = User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True)
        self.fields['service_type'].queryset = ServiceType.objects.filter(is_active=True)
        self.fields['service_type'].empty_label = 'Choose a service'
        self.fields['service_type'].label = 'What are you booking?'
        self.fields['service_type'].help_text = 'Per-photo rates and quote ranges are shown below. Packages receive a final quote from the photographer.'
        self.fields['service_type'].label_from_instance = lambda service: f'{service.name} — {service.price_display}'
        self.fields['photo_count'].label = 'Number of photos'
        self.fields['photo_count'].help_text = 'Required for studio and outdoor shoots; leave blank for other services.'
    def clean(self):
        cleaned = super().clean()
        if self.user and cleaned.get('photographer') == self.user:
            self.add_error('photographer', 'Choose a photographer other than yourself.')
        if cleaned.get('event_date') and cleaned['event_date'] < timezone.localdate():
            self.add_error('event_date', 'Choose a date in the future.')
        if not cleaned.get('service_type'):
            self.add_error('service_type', 'Choose the kind of work you need.')
        elif cleaned['service_type'].pricing_model == ServiceType.PricingModel.PER_PHOTO:
            if not cleaned.get('photo_count'):
                self.add_error('photo_count', 'Add the number of photos for this per-photo service.')
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        service_type = self.cleaned_data['service_type']
        booking.event_type = service_type.name
        if service_type.pricing_model == ServiceType.PricingModel.PER_PHOTO:
            booking.quoted_price = service_type.minimum_price * self.cleaned_data['photo_count']
        else:
            booking.quoted_price = Decimal('0.00')
        if commit:
            booking.save()
        return booking


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ('date', 'is_available', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.TextInput(attrs={'placeholder': 'Optional note for this date'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.localdate():
            raise ValidationError('Availability must be a future date.')
        return date


class BookingStatusForm(forms.Form):
    status = forms.ChoiceField(choices=(
        ('reservation_due', 'Confirm booking'),
        ('balance_due', 'Mark work as finished'),
        ('cancelled', 'Cancel booking'),
    ))
    quoted_price = forms.DecimalField(
        required=False,
        min_value=Decimal('0.00'),
        decimal_places=2,
        max_digits=10,
        label='Final quote (KES)',
    )

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        if booking and booking.quoted_price:
            self.fields['quoted_price'].initial = booking.quoted_price

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') != BookingStatus.RESERVATION_DUE:
            return cleaned

        quote = cleaned.get('quoted_price')
        if not quote or quote <= Decimal('0.00'):
            self.add_error('quoted_price', 'Enter the final quote before accepting this request.')
            return cleaned

        service = self.booking.service_type if self.booking else None
        if service and service.pricing_model == ServiceType.PricingModel.PER_PHOTO:
            expected = service.minimum_price * (self.booking.photo_count or 0)
            if quote != expected:
                self.add_error('quoted_price', f'This service is KES {service.minimum_price:,.0f} per photo for {self.booking.photo_count or 0} photos.')
        elif service:
            if quote < service.minimum_price:
                self.add_error('quoted_price', f'Enter at least KES {service.minimum_price:,.0f}.')
            if service.maximum_price and quote > service.maximum_price:
                self.add_error('quoted_price', f'Enter no more than KES {service.maximum_price:,.0f}.')
        return cleaned
