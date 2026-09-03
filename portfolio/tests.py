from django.test import TestCase

from .models import Album
from users.models import User


class PublicPortfolioTests(TestCase):
    def test_hidden_album_is_not_publicly_viewable(self):
        photographer = User.objects.create_user(
            username='photographer', email='photographer@example.com', password='pass', role=User.Role.PHOTOGRAPHER
        )
        album = Album.objects.create(photographer=photographer, title='Private set', is_public=False)

        response = self.client.get(f'/portfolio/album/{album.pk}/')

        self.assertEqual(response.status_code, 404)
