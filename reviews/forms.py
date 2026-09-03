from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'title', 'body')
        widgets = {
            'rating': forms.Select(choices=[(value, f'{value} / 5') for value in range(1, 6)]),
            'body': forms.Textarea(attrs={'rows': 5, 'placeholder': 'What stood out about working together?'}),
        }