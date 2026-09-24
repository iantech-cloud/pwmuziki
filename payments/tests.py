import json
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from bookings.models import Booking, BookingStatus, ReservationStatus
from users.models import User
from .models import Invoice, Transaction
from .services import initiate_stk_push, normalize_phone_number


class DarajaPhoneTests(SimpleTestCase):
    def test_normalizes_common_kenyan_formats(self):
        self.assertEqual(normalize_phone_number('0712 345 678'), '254712345678')
        self.assertEqual(normalize_phone_number('+254 712 345 678'), '254712345678')

    def test_rejects_non_kenyan_number(self):
        with self.assertRaises(ValueError):
            normalize_phone_number('+1 202 555 0199')

    @override_settings(
        MPESA_CALLBACK_URL='https://example.com/payments/mpesa/callback/',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='passkey',
        MPESA_PARTY_B='123456',
    )
    @patch('payments.services.mpesa_access_token', return_value='token')
    @patch('payments.services._request', return_value={'CheckoutRequestID': 'ws_CO_TEST'})
    def test_stk_payload_uses_public_callback_and_whole_shilling_amount(self, request, access_token):
        response = initiate_stk_push(
            phone_number='0712345678',
            amount=Decimal('2500.00'),
            account_reference='AUR1R',
            description='AuraCity booking 1',
        )

        self.assertEqual(response['CheckoutRequestID'], 'ws_CO_TEST')
        payload = request.call_args.kwargs['payload']
        self.assertEqual(payload['Amount'], 2500)
        self.assertEqual(payload['CallBackURL'], 'https://example.com/payments/mpesa/callback/')
        access_token.assert_called_once()

    @override_settings(
        MPESA_CALLBACK_URL='https://example.com/payments/mpesa/callback/',
        MPESA_SHORTCODE='123456',
        MPESA_PASSKEY='passkey',
    )
    def test_stk_rejects_decimal_kes(self):
        with self.assertRaises(ValueError):
            initiate_stk_push(
                phone_number='0712345678',
                amount=Decimal('2500.50'),
                account_reference='AUR1R',
                description='AuraCity booking 1',
            )


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
            data=json.dumps({
                'Body': {
                    'stkCallback': {
                        'CheckoutRequestID': transaction.provider_reference,
                        'ResultCode': 0,
                        'ResultDesc': 'The service request is processed successfully.',
                        'CallbackMetadata': {
                            'Item': [
                                {'Name': 'Amount', 'Value': float(transaction.amount)},
                                {'Name': 'MpesaReceiptNumber', 'Value': 'QAB1234567'},
                            ],
                        },
                    },
                },
            }),
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

    def test_duplicate_success_callback_is_idempotent(self):
        transaction = Transaction.objects.create(
            invoice=self.invoice,
            payer=self.booking.client,
            amount=Decimal('2000'),
            purpose=Transaction.Purpose.RESERVATION,
            provider_reference='ws_CO_DUPLICATE',
        )
        self.booking.status = BookingStatus.RESERVATION_DUE
        self.booking.save(update_fields=('status', 'updated_at'))

        self.assertEqual(self.callback(transaction).status_code, 200)
        self.assertEqual(self.callback(transaction).status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.SUCCESS)
        self.assertEqual(Transaction.objects.filter(pk=transaction.pk).count(), 1)

    @override_settings(MPESA_ENVIRONMENT='production')
    def test_production_callback_does_not_require_optional_token(self):
        response = self.client.post(
            '/payments/mpesa/callback/',
            data=json.dumps({'Body': {'stkCallback': {}}}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)

    @patch('payments.views.query_stk_push', return_value={'ResultCode': '1032', 'ResultDesc': 'Request canceled by user'})
    def test_payment_status_queries_pending_stk_and_marks_terminal_failure(self, query):
        transaction = Transaction.objects.create(
            invoice=self.invoice,
            payer=self.booking.client,
            amount=Decimal('2000'),
            purpose=Transaction.Purpose.RESERVATION,
            checkout_request_id='ws_CO_QUERY',
            provider_reference='ws_CO_QUERY',
        )
        self.client.force_login(self.booking.client)

        response = self.client.get(f'/payments/transaction/{transaction.pk}/status/')

        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.FAILED)
        query.assert_called_once_with(checkout_request_id='ws_CO_QUERY')

