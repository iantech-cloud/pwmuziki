from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AlbumForm, PhotoForm
from .models import Album, Photo


def album_detail(request, pk):
    album = get_object_or_404(
        Album.objects.filter(is_public=True)
        .select_related('photographer', 'photographer__profile', 'category')
        .prefetch_related('photos'),
        pk=pk,
    )
    return render(request, 'portfolio/album_detail.html', {'album': album})


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
