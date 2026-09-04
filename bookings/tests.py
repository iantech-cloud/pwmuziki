from decimal import Decimal

from django.test import TestCase

from users.models import User
from .models import Booking, BookingStatus, ReservationStatus, ServiceType
from .forms import BookingForm


class BookingLifecycleTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='booking-client',
            email='booking-client@example.com',
            password='pass',
        )
        self.photographer = User.objects.create_user(
            username='booking-photographer',
            email='booking-photographer@example.com',
            password='pass',
            role=User.Role.PHOTOGRAPHER,
        )
        self.service = ServiceType.objects.create(
            name='Test studio shoot',
            slug='test-studio-shoot',
            pricing_model=ServiceType.PricingModel.PER_PHOTO,
            minimum_price=Decimal('150.00'),
            maximum_price=Decimal('150.00'),
            unit_label='photo',
        )

    def make_booking(self, status=BookingStatus.PENDING, reservation_status=ReservationStatus.DUE):
        return Booking.objects.create(
            client=self.client_user,
            photographer=self.photographer,
            service_type=self.service,
            photo_count=100,
            event_date='2030-01-01',
            event_type=self.service.name,
            location='Nairobi',
            quoted_price=self.service.minimum_price * 100,
            status=status,
            reservation_status=reservation_status,
        )

    def test_booking_uses_service_quote_and_calculates_twenty_percent_reservation(self):
        form = BookingForm(
            data={
                'photographer': self.photographer.pk,
                'service_type': self.service.pk,
                'photo_count': 100,
                'event_date': '2030-01-01',
                'location': 'Nairobi',
                'details': 'Portrait session',
            },
            user=self.client_user,
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        booking = form.save(commit=False)
        booking.client = self.client_user
        booking.save()

        self.assertEqual(booking.event_type, 'Test studio shoot')
        self.assertEqual(booking.quoted_price, Decimal('15000.00'))
        self.assertEqual(booking.reservation_fee, Decimal('3000.00'))
        self.assertEqual(booking.balance, Decimal('12000.00'))

    def test_catalog_uses_photo_rates_and_open_quote_ranges(self):
        studio = ServiceType.objects.get(slug='studio-shoot')
        outdoor = ServiceType.objects.get(slug='outdoor-shoot')
        reels = ServiceType.objects.get(slug='reels-package')
        wedding = ServiceType.objects.get(slug='wedding-coverage')

        self.assertEqual(studio.pricing_model, ServiceType.PricingModel.PER_PHOTO)
        self.assertEqual(studio.minimum_price, Decimal('150.00'))
        self.assertEqual(outdoor.minimum_price, Decimal('200.00'))
        self.assertEqual(reels.minimum_price, Decimal('1000.00'))
        self.assertEqual(reels.maximum_price, Decimal('80000.00'))
        self.assertEqual(wedding.minimum_price, Decimal('10000.00'))
        self.assertEqual(wedding.maximum_price, Decimal('80000.00'))

    def test_client_can_send_service_booking_request(self):
        self.client.force_login(self.client_user)

        response = self.client.post('/bookings/new/', {
            'photographer': self.photographer.pk,
            'service_type': self.service.pk,
            'photo_count': 100,
            'event_date': '2030-01-01',
            'location': 'Nairobi',
            'details': 'Portrait session',
        })

        self.assertRedirects(response, '/bookings/')
        booking = Booking.objects.get(client=self.client_user)
        self.assertEqual(booking.event_type, self.service.name)
        self.assertEqual(booking.quoted_price, Decimal('15000.00'))
        self.assertEqual(booking.reservation_fee, Decimal('3000.00'))

    def test_client_confirmation_releases_held_reservation(self):
        booking = self.make_booking(
            status=BookingStatus.RESERVED,
            reservation_status=ReservationStatus.HELD,
        )
        self.client.force_login(self.client_user)

        response = self.client.post(f'/bookings/{booking.pk}/confirm-arrival/')

        booking.refresh_from_db()
        self.assertRedirects(response, f'/bookings/{booking.pk}/')
        self.assertEqual(booking.status, BookingStatus.ARRIVAL_CONFIRMED)
        self.assertEqual(booking.reservation_status, ReservationStatus.RELEASED)
        self.assertIsNotNone(booking.arrival_confirmed_at)

    def test_photographer_can_mark_arrival_confirmed_work_as_finished(self):
        booking = self.make_booking(status=BookingStatus.ARRIVAL_CONFIRMED)
        self.client.force_login(self.photographer)

        response = self.client.post(
            f'/bookings/{booking.pk}/status/',
            {'status': BookingStatus.BALANCE_DUE},
        )

        booking.refresh_from_db()
        self.assertRedirects(response, f'/bookings/{booking.pk}/')
        self.assertEqual(booking.status, BookingStatus.BALANCE_DUE)
        self.assertIsNotNone(booking.work_completed_at)

# Create your tests here.
