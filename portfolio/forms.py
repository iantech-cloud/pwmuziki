from django import forms

from bookings.models import Booking
from .models import Album, DeliveryPhoto, Photo


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ('title', 'category', 'description', 'is_public')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What does this body of work hold?'}),
        }


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ('image', 'caption', 'watermark_text', 'licensing_info', 'is_preview', 'is_featured')
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'A short caption'}),
            'watermark_text': forms.TextInput(attrs={'placeholder': 'Optional watermark text'}),
            'licensing_info': forms.TextInput(attrs={'placeholder': 'Usage or licensing notes'}),
        }


class DeliveryPhotoForm(forms.ModelForm):
    class Meta:
        model = DeliveryPhoto
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Preview caption'}),
        }


class DeliverySettingsForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('google_drive_url', 'delivery_note')
        widgets = {
            'google_drive_url': forms.URLInput(attrs={'placeholder': 'https://drive.google.com/drive/folders/...'}),
            'delivery_note': forms.Textarea(attrs={'rows': 4, 'placeholder': 'A note for the client about their finished gallery.'}),
        }