from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import RegistrationForm
from .models import Profile, User


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'registration/register.html', {'form': form})

def home(request):
    photographers = User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True).select_related('profile')
    return render(request, 'home.html', {'photographers': photographers})

@login_required
def dashboard(request):
    bookings = request.user.client_bookings.all() if request.user.role == User.Role.CLIENT else request.user.photographer_bookings.all()
    return render(request, 'dashboard.html', {'bookings': bookings[:8], 'profile': Profile.ensure_for(request.user)})
