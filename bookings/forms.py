from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User
from .models import Availability, Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('photographer', 'event_date', 'event_type', 'location', 'details', 'quoted_price', 'deposit_amount')
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Share the mood, timing, and anything else that matters...'}),
        }
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['photographer'].queryset = User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True)
        self.fields['quoted_price'].min_value = 0
        self.fields['deposit_amount'].min_value = 0
    def clean(self):
        cleaned = super().clean()
        if self.user and cleaned.get('photographer') == self.user:
            self.add_error('photographer', 'Choose a photographer other than yourself.')
        if cleaned.get('event_date') and cleaned['event_date'] < timezone.localdate():
            self.add_error('event_date', 'Choose a date in the future.')
        if cleaned.get('quoted_price') is not None and cleaned.get('deposit_amount') is not None:
            if cleaned['deposit_amount'] > cleaned['quoted_price']:
                self.add_error('deposit_amount', 'The deposit cannot be greater than the quoted price.')
        return cleaned


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
        ('confirmed', 'Confirm booking'),
        ('completed', 'Mark as completed'),
        ('cancelled', 'Cancel booking'),
    ))
