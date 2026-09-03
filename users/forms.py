from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(
        required=True,
        choices=(
            ('', 'Choose how you’ll use Pwmuziki'),
            (User.Role.CLIENT, 'I’m booking a photographer'),
            (User.Role.PHOTOGRAPHER, 'I’m sharing my photography'),
        ),
        widget=forms.Select,
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, initial_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete = {
            'username': 'username',
            'email': 'email',
            'first_name': 'given-name',
            'last_name': 'family-name',
            'password1': 'new-password',
            'password2': 'new-password',
        }
        for name, value in autocomplete.items():
            self.fields[name].widget.attrs['autocomplete'] = value
        if initial_role in User.Role.values:
            self.fields['role'].initial = initial_role


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'bio', 'portfolio_link', 'phone_number', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell people what you love to photograph...'}),
            'portfolio_link': forms.URLInput(attrs={'placeholder': 'https://your-portfolio.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254 700 000 000'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save(update_fields=['first_name', 'last_name'])
        if commit:
            profile.save()
        return profile
