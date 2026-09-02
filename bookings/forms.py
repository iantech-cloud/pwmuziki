from django import forms
from users.models import User
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('photographer', 'event_date', 'event_type', 'location', 'details', 'quoted_price', 'deposit_amount')
        widgets = {'event_date': forms.DateInput(attrs={'type': 'date'})}
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['photographer'].queryset = User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True)
    def clean(self):
        cleaned = super().clean()
        if self.user and cleaned.get('photographer') == self.user:
            self.add_error('photographer', 'Choose a photographer other than yourself.')
        return cleaned
