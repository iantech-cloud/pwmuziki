from django.shortcuts import get_object_or_404, render

from .models import Album


def album_detail(request, pk):
    album = get_object_or_404(
        Album.objects.filter(is_public=True)
        .select_related('photographer', 'photographer__profile', 'category')
        .prefetch_related('photos'),
        pk=pk,
    )
    return render(request, 'portfolio/album_detail.html', {'album': album})
