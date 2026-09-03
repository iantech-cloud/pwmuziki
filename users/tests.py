from django.test import TestCase

from .models import Profile, User


class FeaturedDirectoryTests(TestCase):
    def test_featured_photographers_are_listed_first(self):
        regular = User.objects.create_user(username='regular', email='regular@example.com', password='pass', role=User.Role.PHOTOGRAPHER)
        featured = User.objects.create_user(username='featured', email='featured@example.com', password='pass', role=User.Role.PHOTOGRAPHER)
        Profile.objects.filter(user=featured).update(is_featured=True)

        response = self.client.get('/')

        photographers = response.context['photographers']
        self.assertEqual(photographers[0], featured)
        self.assertEqual(photographers[1], regular)
