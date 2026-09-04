import json
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from bookings.models import Booking, BookingStatus, ReservationStatus
from users.models import User
from .models import Invoice, Transaction
from .services import normalize_phone_number


class DarajaPhoneTests(SimpleTestCase):
    def test_normalizes_common_kenyan_formats(self):
        self.assertEqual(normalize_phone_number('0712 345 678'), '254712345678')
        self.assertEqual(normalize_phone_number('+254 712 345 678'), '254712345678')

    def test_rejects_non_kenyan_number(self):
        with self.assertRaises(ValueError):
            normalize_phone_number('+1 202 555 0199')


class DarajaCallbackTests(TestCase):
    def setUp(self):
        client = User.objects.create_user(username='client', email='client@example.com', password='pass')
        photographer = User.objects.create_user(
            username='photographer', email='photographer@example.com', password='pass', role=User.Role.PHOTOGRAPHER
        )
        self.booking = Booking.objects.create(
            client=client,
            photographer=photographer,
            event_date='2030-01-01',
            event_type='Portrait',
            location='Nairobi',
            quoted_price=Decimal('10000'),
        )
        self.invoice = Invoice.objects.create(
            booking=self.booking,
            number='PWM-TEST-1',
            total_amount=Decimal('10000'),
            reservation_amount=Decimal('2000'),
            balance_amount=Decimal('8000'),
        )

    def callback(self, transaction):
        return self.client.post(
            '/payments/mpesa/callback/',
            data=json.dumps({'Body': {'stkCallback': {'CheckoutRequestID': transaction.provider_reference, 'ResultCode': 0}}}),
            content_type='application/json',
        )

    def test_reservation_callback_holds_twenty_percent_in_escrow(self):
        transaction = Transaction.objects.create(
            invoice=self.invoice,
            payer=self.booking.client,
            amount=Decimal('2000'),
            purpose=Transaction.Purpose.RESERVATION,
            provider_reference='ws_CO_RESERVATION',
        )
        self.booking.status = BookingStatus.RESERVATION_DUE
        self.booking.save(update_fields=('status', 'updated_at'))

        response = self.callback(transaction)

        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.invoice.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)
        self.assertTrue(self.invoice.reservation_paid)
        self.assertFalse(self.invoice.is_paid)
        self.assertEqual(self.booking.status, BookingStatus.RESERVED)
        self.assertEqual(self.booking.reservation_status, ReservationStatus.HELD)

    def test_balance_callback_completes_booking_after_final_payment(self):
        transaction = Transaction.objects.create(
            invoice=self.invoice,
            payer=self.booking.client,
            amount=Decimal('8000'),
            purpose=Transaction.Purpose.BALANCE,
            provider_reference='ws_CO_TEST',
        )
        self.booking.status = BookingStatus.BALANCE_DUE
        self.booking.save(update_fields=('status', 'updated_at'))
        response = self.callback(transaction)

        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.invoice.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)
        self.assertTrue(self.invoice.is_paid)
        self.assertTrue(self.invoice.balance_paid)
        self.assertEqual(self.booking.status, BookingStatus.COMPLETED)
