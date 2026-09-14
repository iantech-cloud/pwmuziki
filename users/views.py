from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg, Prefetch
from django.utils import timezone
from reviews.models import Review
from .forms import ProfileForm, RegistrationForm
from .models import ClientNote, Contract, GalleryAccess, MessageThread, Profile, StudioSettings, User
from portfolio.models import Album, Photo


def register(request):
    return _register(request)


def register_as(request, role):
    if role not in User.Role.values:
        from django.http import Http404
        raise Http404
    return _register(request, role)


def register_client(request):
    return register_as(request, User.Role.CLIENT)


def register_photographer(request):
    return register_as(request, User.Role.PHOTOGRAPHER)


def _register(request, initial_role=None):
    form = RegistrationForm(request.POST or None, initial_role=initial_role)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        from .email_utils import send_welcome_email
        send_welcome_email(user)
        login(request, user)
        return redirect('dashboard')
    role = form['role'].value()
    return render(request, 'registration/register.html', {
        'form': form,
        'selected_role': role,
        'selected_role_label': dict(User.Role.choices).get(role),
    })

def home(request):
    photographers = (
        User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True)
        .select_related('profile')
        .prefetch_related(
            Prefetch(
                'albums',
                queryset=Album.objects.filter(is_public=True).prefetch_related(
                    Prefetch('photos', queryset=Photo.objects.order_by('-uploaded_at'))
                ),
                to_attr='public_albums',
            )
        )
        .order_by('-profile__is_featured', '-date_joined')
    )
    return render(request, 'home.html', {'photographers': photographers})


def photographer_detail(request, pk):
    photographer = get_object_or_404(
        User.objects.filter(role=User.Role.PHOTOGRAPHER, is_active=True).select_related('profile'),
        pk=pk,
    )
    albums = (
        Album.objects.filter(photographer=photographer, is_public=True)
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('-uploaded_at')))
        .order_by('-created_at')
    )
    reviews = Review.objects.filter(photographer=photographer).select_related('client')
    average_rating = reviews.aggregate(average=Avg('rating'))['average']
    return render(request, 'photographers/detail.html', {
        'photographer': photographer,
        'albums': albums,
        'reviews': reviews,
        'average_rating': average_rating,
    })


@login_required
def dashboard(request):
    bookings = (
        request.user.client_bookings.all()
        if request.user.role == User.Role.CLIENT
        else request.user.photographer_bookings.all()
    ).select_related('client', 'photographer')
    profile = Profile.ensure_for(request.user)
    context = {'bookings': bookings[:8], 'profile': profile}
    today = timezone.localdate()
    context['upcoming_count'] = bookings.filter(event_date__gte=today).exclude(status='cancelled').count()
    if request.user.role == User.Role.PHOTOGRAPHER:
        context['portfolio_albums'] = Album.objects.filter(photographer=request.user).prefetch_related('photos').order_by('-created_at')
        context['pending_count'] = bookings.filter(status='pending').count()
        context['confirmed_count'] = bookings.filter(status__in=['reservation_due', 'reserved', 'arrival_confirmed', 'balance_due']).count()
        context['published_count'] = Album.objects.filter(photographer=request.user, is_public=True).count()
        context['client_count'] = bookings.values('client_id').distinct().count()
        context['notes'] = ClientNote.objects.filter(photographer=request.user).select_related('client__profile')[:5]
        context['gallery_count'] = GalleryAccess.objects.filter(album__photographer=request.user).count()
        context['contract_count'] = Contract.objects.filter(booking__photographer=request.user).count()
        context['threads'] = MessageThread.objects.filter(photographer=request.user).select_related('client__profile')[:5]
        context['studio_settings'] = StudioSettings.objects.filter(photographer=request.user).first()
    else:
        context['awaiting_count'] = bookings.filter(status='pending').count()
        context['balance_due'] = sum((booking.balance for booking in bookings.filter(status='balance_due')), 0)
        context['galleries'] = GalleryAccess.objects.filter(client=request.user).select_related('album', 'album__photographer__profile')[:5]
        context['contracts'] = Contract.objects.filter(booking__client=request.user).select_related('booking')[:5]
        context['threads'] = MessageThread.objects.filter(client=request.user).select_related('photographer__profile')[:5]
    return render(request, 'dashboard.html', context)


@login_required
def profile_edit(request):
    profile = Profile.ensure_for(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'profile/edit.html', {'form': form, 'profile': profile})
