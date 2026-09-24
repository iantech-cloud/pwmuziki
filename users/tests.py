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
        self.assertContains(response, 'Choose how you’ll use AuraCity')
        self.assertFalse(User.objects.filter(username='no-role').exists())

    def test_client_registration_logs_into_client_dashboard(self):
        data = self.registration_data('new-client')
        data['role'] = User.Role.CLIENT

        response = self.client.post('/register/client/', data)

        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertEqual(response.wsgi_request.user.role, User.Role.CLIENT)
        dashboard_response = self.client.get('/dashboard/')
        self.assertRedirects(dashboard_response, '/client/dashboard/')
        self.assertEqual(User.objects.get(username='new-client').role, User.Role.CLIENT)
        self.assertEqual(response.wsgi_request.user.role, User.Role.CLIENT)

    def test_photographer_registration_logs_into_photographer_dashboard(self):
        data = self.registration_data('new-photographer')
        data['role'] = User.Role.PHOTOGRAPHER

        response = self.client.post('/register/photographer/', data)

        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertEqual(response.wsgi_request.user.role, User.Role.PHOTOGRAPHER)
        dashboard_response = self.client.get('/dashboard/')
        self.assertRedirects(dashboard_response, '/photographer/dashboard/')
        self.assertEqual(User.objects.get(username='new-photographer').role, User.Role.PHOTOGRAPHER)
        self.assertEqual(response.wsgi_request.user.role, User.Role.PHOTOGRAPHER)


class DashboardFlowTests(TestCase):
    def test_client_dashboard_renders_client_actions(self):
        user = User.objects.create_user(username='client-dashboard', email='client-dashboard@example.com', password='pass')
        self.client.force_login(user)

        response = self.client.get('/client/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request a booking')
        self.assertContains(response, 'Browse photographers')

    def test_dashboard_dispatches_to_canonical_client_route(self):
        user = User.objects.create_user(username='client-dispatch', email='client-dispatch@example.com', password='pass')
        self.client.force_login(user)

        response = self.client.get('/dashboard/')

        self.assertRedirects(response, '/client/dashboard/')

    def test_dashboard_dispatches_to_canonical_photographer_route(self):
        user = User.objects.create_user(username='photographer-dispatch', email='photographer-dispatch@example.com', password='pass', role=User.Role.PHOTOGRAPHER)
        self.client.force_login(user)

        response = self.client.get('/dashboard/')

        self.assertRedirects(response, '/photographer/dashboard/')

    def test_photographer_dashboard_renders_work_actions(self):
        user = User.objects.create_user(
            username='photographer-dashboard',
            email='photographer-dashboard@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        self.client.force_login(user)

        response = self.client.get('/photographer/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage portfolio')
        self.assertContains(response, 'Set availability')
