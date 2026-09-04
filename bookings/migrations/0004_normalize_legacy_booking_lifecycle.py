from decimal import Decimal

from django.db import migrations


def normalize_legacy_bookings(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')

    for booking in Booking.objects.all():
        booking.reservation_fee = (booking.quoted_price * Decimal('0.20')).quantize(Decimal('0.01'))
        booking.deposit_amount = booking.reservation_fee
        if booking.status == 'confirmed':
            booking.status = 'reservation_due'
        elif booking.status == 'completed':
            booking.status = 'balance_due'
        booking.save(update_fields=('reservation_fee', 'deposit_amount', 'status', 'updated_at'))


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0003_servicetype_booking_arrival_confirmed_at_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_legacy_bookings, migrations.RunPython.noop),
    ]