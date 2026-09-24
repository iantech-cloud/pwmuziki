from django.test import TestCase

from .models import Album
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
