from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg, Prefetch
from django.utils import timezone
from reviews.models import Review
from .forms import ClientNoteForm, MessageForm, ProfileForm, RegistrationForm
from .models import ClientNote, Contract, GalleryAccess, MessageThread, Notification, Profile, StudioSettings, User
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


def _dashboard_context(request):
    bookings = (
        request.user.client_bookings.all()
        if request.user.role == User.Role.CLIENT
        else request.user.photographer_bookings.all()
    ).select_related('client', 'photographer')
    profile = Profile.ensure_for(request.user)
    context = {
        'bookings': bookings[:8],
        'profile': profile,
        'notifications': Notification.objects.filter(recipient=request.user)[:6],
        'unread_notifications': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    }
    today = timezone.localdate()
    context['upcoming_count'] = bookings.filter(event_date__gte=today).exclude(status='cancelled').count()
    if request.user.role == User.Role.PHOTOGRAPHER:
        context.update({
            'portfolio_albums': Album.objects.filter(photographer=request.user).prefetch_related('photos').order_by('-created_at'),
            'pending_count': bookings.filter(status='pending').count(),
            'gallery_count': GalleryAccess.objects.filter(album__photographer=request.user).count(),
        })
    else:
        context.update({
            'awaiting_count': bookings.filter(status='pending').count(),
            'balance_due': sum((booking.balance for booking in bookings.filter(status='balance_due')), 0),
            'galleries': GalleryAccess.objects.filter(client=request.user).select_related('album', 'album__photographer__profile')[:5],
        })
    return context


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
    if request.user.role == User.Role.PHOTOGRAPHER:
        return render(request, 'dashboard_photographer.html', _dashboard_context(request))
    return render(request, 'dashboard_client.html', _dashboard_context(request))


@login_required
def photographer_dashboard(request):
    if request.user.role != User.Role.PHOTOGRAPHER:
        return redirect('client_dashboard')
    return render(request, 'dashboard_photographer.html', _dashboard_context(request))


@login_required
def client_dashboard(request):
    if request.user.role != User.Role.CLIENT:
        return redirect('photographer_dashboard')
    return render(request, 'dashboard_client.html', _dashboard_context(request))


@login_required
def create_client_note(request):
    if request.user.role != User.Role.PHOTOGRAPHER:
        return redirect('dashboard')
    form = ClientNoteForm(request.POST or None)
    form.fields['client'].queryset = User.objects.filter(client_bookings__photographer=request.user).distinct()
    if request.method == 'POST' and form.is_valid():
        note = form.save(commit=False)
        note.photographer = request.user
        note.save()
        return redirect('dashboard')
    return render(request, 'dashboard_action.html', {'form': form, 'eyebrow': 'Client management', 'heading': 'Add a client note.', 'submit_label': 'Save note'})


@login_required
def send_message(request, thread_id=None):
    if request.method != 'POST':
        return redirect('dashboard')
    thread = get_object_or_404(MessageThread, pk=thread_id)
    if request.user not in (thread.client, thread.photographer):
        return redirect('dashboard')
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.thread = thread
        message.sender = request.user
        message.save()
        MessageThread.objects.filter(pk=thread.pk).update(updated_at=timezone.now())
    return redirect('dashboard')


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'Notifications marked as read.')
    return redirect('dashboard')


@login_required
def profile_edit(request):
    profile = Profile.ensure_for(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'profile/edit.html', {'form': form, 'profile': profile})
