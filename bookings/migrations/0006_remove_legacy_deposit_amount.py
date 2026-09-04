from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0005_service_pricing_and_photo_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='deposit_amount',
        ),
    ]