from django import forms

from .models import Album, Photo


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
        fields = ('image', 'caption', 'watermark_text', 'licensing_info', 'is_preview')
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'A short caption'}),
            'watermark_text': forms.TextInput(attrs={'placeholder': 'Optional watermark text'}),
            'licensing_info': forms.TextInput(attrs={'placeholder': 'Usage or licensing notes'}),
        }