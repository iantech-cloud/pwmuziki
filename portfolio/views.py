import mimetypes
import os
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from urllib.parse import urlparse
from django.utils import timezone
from django.utils._os import safe_join

from .forms import AlbumForm, DeliveryPhotoForm, DeliverySettingsForm, PhotoForm
from .models import Album, DeliveryPhoto, Photo
from users.models import GalleryAccess, Profile


def media_file(request, path):
    """Serve uploads only when the related portfolio or booking permits access."""
    media_path = path.lstrip('/')
    try:
        absolute_path = safe_join(settings.MEDIA_ROOT, media_path)
    except ValueError as exc:
        raise Http404 from exc
    if not os.path.isfile(absolute_path):
        raise Http404

    photo = Photo.objects.filter(
        Q(image=media_path) | Q(branded_image=media_path),
    ).select_related('album__photographer').first()
    delivery_photo = DeliveryPhoto.objects.filter(
        image=media_path,
    ).select_related('booking__client', 'booking__photographer').first()
    profile = Profile.objects.filter(avatar=media_path).select_related('user').first()

    is_public = False
    is_authorized = False
    if photo:
        is_public = photo.album.is_public and photo.album.photographer.is_active
        is_authorized = is_public or (
            request.user.is_authenticated
            and request.user.id == photo.album.photographer_id
        )
        if (
            not is_authorized
            and request.user.is_authenticated
            and request.user.role == 'client'
        ):
            is_authorized = GalleryAccess.objects.filter(
                album=photo.album,
                client=request.user,
                is_published=True,
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()),
            ).exists()
    elif delivery_photo:
        is_authorized = request.user.is_authenticated and request.user.id in {
            delivery_photo.booking.client_id,
            delivery_photo.booking.photographer_id,
        }
    elif profile:
        is_public = profile.user.role == 'photographer' and profile.user.is_active
        is_authorized = is_public or (
            request.user.is_authenticated and request.user.id == profile.user_id
        )
    else:
        raise Http404

    if not is_authorized:
        raise Http404

    response = FileResponse(
        open(absolute_path, 'rb'),
        content_type=mimetypes.guess_type(absolute_path)[0] or 'application/octet-stream',
    )
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(media_path)}"'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'public, max-age=3600' if is_public else 'private, no-store'
    return response


def gallery(request):
    photos = Photo.objects.filter(
        is_featured=True,
        album__is_public=True,
        album__photographer__is_active=True,
    ).select_related('album', 'album__photographer', 'album__photographer__profile').order_by('-uploaded_at')
    return render(request, 'portfolio/gallery.html', {'photos': photos})


def album_detail(request, pk):
    album = get_object_or_404(
        Album.objects.filter(is_public=True)
        .select_related('photographer', 'photographer__profile', 'category')
        .prefetch_related('photos'),
        pk=pk,
    )
    return render(request, 'portfolio/album_detail.html', {'album': album})


@login_required
def private_album_detail(request, pk):
    if request.user.role != 'client':
        raise Http404
    access = get_object_or_404(
        GalleryAccess.objects.filter(
            client=request.user,
            album_id=pk,
            is_published=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()),
        ).select_related('album__photographer', 'album__photographer__profile', 'album__category'),
    )
    album = access.album
    album._private_gallery_access = access
    photos = Photo.objects.filter(album=album).order_by('-uploaded_at')
    album._prefetched_objects_cache = {'photos': list(photos)}
    return render(request, 'portfolio/private_album_detail.html', {'album': album, 'gallery_access': access})


@login_required
def portfolio_manage(request):
    if request.user.role != 'photographer':
        return redirect('dashboard')
    albums = Album.objects.filter(photographer=request.user).prefetch_related('photos').order_by('-created_at')
    return render(request, 'portfolio/manage.html', {'albums': albums})


@login_required
def album_create(request):
    if request.user.role != 'photographer':
        return redirect('dashboard')
    form = AlbumForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        album = form.save(commit=False)
        album.photographer = request.user
        album.save()
        return redirect('portfolio_manage')
    return render(request, 'portfolio/album_form.html', {'form': form})


@login_required
def photo_upload(request, album_id):
    album = get_object_or_404(Album, pk=album_id, photographer=request.user)
    form = PhotoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        photo = form.save(commit=False)
        photo.album = album
        photo.save()
        return redirect('portfolio_manage')
    return render(request, 'portfolio/photo_form.html', {'form': form, 'album': album})


@login_required
def album_toggle_public(request, pk):
    album = get_object_or_404(Album, pk=pk, photographer=request.user)
    if request.method == 'POST':
        album.is_public = not album.is_public
        album.save(update_fields=['is_public'])
    return redirect('portfolio_manage')


@login_required
def delivery_manage(request, booking_id):
    if request.user.role != 'photographer':
        raise Http404
    from bookings.models import Booking
    booking = get_object_or_404(
        Booking.objects.select_related('client', 'photographer'),
        pk=booking_id,
        photographer=request.user,
    )
    settings_form = DeliverySettingsForm(request.POST or None, instance=booking)
    photo_form = DeliveryPhotoForm()
    if request.method == 'POST':
        if 'save_delivery' in request.POST and settings_form.is_valid():
            booking = settings_form.save(commit=False)
            if booking.google_drive_url:
                booking.delivery_ready_at = timezone.now()
            booking.save(update_fields=['google_drive_url', 'delivery_note', 'delivery_ready_at', 'updated_at'])
            return redirect('delivery_manage', booking_id=booking.pk)
        if 'upload_preview' in request.POST:
            photo_form = DeliveryPhotoForm(request.POST, request.FILES)
            if photo_form.is_valid():
                preview = photo_form.save(commit=False)
                preview.booking = booking
                preview.save()
                return redirect('delivery_manage', booking_id=booking.pk)
    return render(request, 'portfolio/delivery_manage.html', {
        'booking': booking,
        'settings_form': settings_form,
        'photo_form': photo_form,
        'delivery_photos': booking.delivery_photos.order_by('-uploaded_at'),
    })


@login_required
def delivery_link(request, booking_id):
    from bookings.models import BookingStatus, Booking
    booking = get_object_or_404(Booking, pk=booking_id, client=request.user)
    if booking.status != BookingStatus.COMPLETED or not booking.google_drive_url:
        raise Http404
    parsed_url = urlparse(booking.google_drive_url)
    if parsed_url.scheme != 'https' or parsed_url.hostname not in {'drive.google.com', 'docs.google.com'}:
        raise Http404
    return redirect(booking.google_drive_url)
