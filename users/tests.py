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


class RegistrationFlowTests(TestCase):
    def registration_data(self, username):
        return {
            'username': username,
            'email': f'{username}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'A-strong-password-123!',
            'password2': 'A-strong-password-123!',
        }

    def test_generic_registration_requires_an_explicit_role(self):
        response = self.client.post('/register/', self.registration_data('no-role'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose how you’ll use Pwmuziki')
        self.assertFalse(User.objects.filter(username='no-role').exists())

    def test_client_registration_logs_into_client_dashboard(self):
        data = self.registration_data('new-client')
        data['role'] = User.Role.CLIENT

        response = self.client.post('/register/client/', data)

        self.assertRedirects(response, '/dashboard/')
        self.assertEqual(User.objects.get(username='new-client').role, User.Role.CLIENT)
        self.assertEqual(response.wsgi_request.user.role, User.Role.CLIENT)

    def test_photographer_registration_logs_into_photographer_dashboard(self):
        data = self.registration_data('new-photographer')
        data['role'] = User.Role.PHOTOGRAPHER

        response = self.client.post('/register/photographer/', data)

        self.assertRedirects(response, '/dashboard/')
        self.assertEqual(User.objects.get(username='new-photographer').role, User.Role.PHOTOGRAPHER)
        self.assertEqual(response.wsgi_request.user.role, User.Role.PHOTOGRAPHER)


class DashboardFlowTests(TestCase):
    def test_client_dashboard_renders_client_actions(self):
        user = User.objects.create_user(username='client-dashboard', email='client-dashboard@example.com', password='pass')
        self.client.force_login(user)

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request a booking')
        self.assertContains(response, 'Browse photographers')

    def test_photographer_dashboard_renders_work_actions(self):
        user = User.objects.create_user(
            username='photographer-dashboard',
            email='photographer-dashboard@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        self.client.force_login(user)

        response = self.client.get('/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage portfolio')
        self.assertContains(response, 'Set availability')
