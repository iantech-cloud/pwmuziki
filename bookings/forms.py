from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from .models import Availability, Booking, ServiceType

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('photographer', 'service_type', 'event_date', 'location', 'details')
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
        self.fields['service_type'].help_text = 'Suggested starting prices are shown below. The photographer can adjust the final quote.'
        self.fields['service_type'].label_from_instance = (
            lambda service: f'{service.name} — KES {service.suggested_price:,.0f}'
        )
    def clean(self):
        cleaned = super().clean()
        if self.user and cleaned.get('photographer') == self.user:
            self.add_error('photographer', 'Choose a photographer other than yourself.')
        if cleaned.get('event_date') and cleaned['event_date'] < timezone.localdate():
            self.add_error('event_date', 'Choose a date in the future.')
        if not cleaned.get('service_type'):
            self.add_error('service_type', 'Choose the kind of work you need.')
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        service_type = self.cleaned_data['service_type']
        booking.event_type = service_type.name
        booking.quoted_price = service_type.suggested_price
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
