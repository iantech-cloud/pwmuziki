from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from .models import Album, Photo
from users.models import GalleryAccess, User


class PublicPortfolioTests(TestCase):
    def test_hidden_album_is_not_publicly_viewable(self):
        photographer = User.objects.create_user(
            username='photographer', email='photographer@example.com', password='pass', role=User.Role.PHOTOGRAPHER
        )
        album = Album.objects.create(photographer=photographer, title='Private set', is_public=False)

        response = self.client.get(f'/portfolio/album/{album.pk}/')

        self.assertEqual(response.status_code, 404)

    def test_private_gallery_requires_matching_client_access(self):
        photographer = User.objects.create_user(
            username='private-photographer',
            email='private-photographer@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        client = User.objects.create_user(
            username='private-client',
            email='private-client@example.com',
            password='pass',
            role=User.Role.CLIENT,
        )
        other_client = User.objects.create_user(
            username='other-client',
            email='other-client@example.com',
            password='pass',
            role=User.Role.CLIENT,
        )
        album = Album.objects.create(photographer=photographer, title='Client set', is_public=False)
        GalleryAccess.objects.create(album=album, client=client, is_published=True)

        self.client.force_login(other_client)
        self.assertEqual(self.client.get(f'/portfolio/album/{album.pk}/private/').status_code, 404)

        self.client.force_login(client)
        self.assertEqual(self.client.get(f'/portfolio/album/{album.pk}/private/').status_code, 200)

    def test_private_photo_file_requires_active_gallery_access(self):
        photographer = User.objects.create_user(
            username='media-photographer',
            email='media-photographer@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        client = User.objects.create_user(
            username='media-client',
            email='media-client@example.com',
            password='pass',
            role=User.Role.CLIENT,
        )
        other_client = User.objects.create_user(
            username='media-other-client',
            email='media-other-client@example.com',
            password='pass',
            role=User.Role.CLIENT,
        )
        album = Album.objects.create(photographer=photographer, title='Private files', is_public=False)
        photo = Photo.objects.create(
            album=album,
            image=SimpleUploadedFile('private-photo.jpg', b'private-photo'),
        )
        media_url = f'/media/{photo.image.name}'
        try:
            self.assertEqual(self.client.get(media_url).status_code, 404)

            self.client.force_login(other_client)
            self.assertEqual(self.client.get(media_url).status_code, 404)

            GalleryAccess.objects.create(album=album, client=client, is_published=True)
            self.client.force_login(client)
            response = self.client.get(media_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(b''.join(response.streaming_content), b'private-photo')

            GalleryAccess.objects.filter(album=album).update(
                expires_at=timezone.now() - timedelta(minutes=1),
            )
            self.assertEqual(self.client.get(media_url).status_code, 404)
        finally:
            photo.image.delete(save=False)

    def test_public_photo_file_remains_viewable(self):
        photographer = User.objects.create_user(
            username='public-media-photographer',
            email='public-media-photographer@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        album = Album.objects.create(photographer=photographer, title='Public files', is_public=True)
        photo = Photo.objects.create(
            album=album,
            image=SimpleUploadedFile('public-photo.jpg', b'public-photo'),
        )
        try:
            response = self.client.get(f'/media/{photo.image.name}')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Cache-Control'], 'public, max-age=3600')
            self.assertEqual(b''.join(response.streaming_content), b'public-photo')
        finally:
            photo.image.delete(save=False)
