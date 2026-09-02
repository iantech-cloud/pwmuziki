from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=User.Role.choices)
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'first_name', 'last_name', 'password1', 'password2')
