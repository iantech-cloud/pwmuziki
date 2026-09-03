import json
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from bookings.models import Booking
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
    def test_success_callback_marks_invoice_paid(self):
        client = User.objects.create_user(username='client', email='client@example.com', password='pass')
        photographer = User.objects.create_user(
            username='photographer', email='photographer@example.com', password='pass', role=User.Role.PHOTOGRAPHER
        )
        booking = Booking.objects.create(
            client=client,
            photographer=photographer,
            event_date='2030-01-01',
            event_type='Portrait',
            location='Nairobi',
            quoted_price=Decimal('10000'),
            deposit_amount=Decimal('2000'),
        )
        invoice = Invoice.objects.create(booking=booking, number='PWM-TEST-1', total_amount=Decimal('8000'))
        transaction = Transaction.objects.create(
            invoice=invoice,
            payer=client,
            amount=Decimal('8000'),
            provider_reference='ws_CO_TEST',
        )

        response = self.client.post(
            '/payments/mpesa/callback/',
            data=json.dumps({'Body': {'stkCallback': {'CheckoutRequestID': transaction.provider_reference, 'ResultCode': 0}}}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        invoice.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)
        self.assertTrue(invoice.is_paid)
