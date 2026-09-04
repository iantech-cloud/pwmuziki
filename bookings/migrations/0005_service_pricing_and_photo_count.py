from decimal import Decimal

from django.db import migrations, models


def convert_service_pricing(apps, schema_editor):
    ServiceType = apps.get_model('bookings', 'ServiceType')

    for service in ServiceType.objects.all():
        if service.slug == 'studio-shoot':
            pricing_model = 'per_photo'
            minimum = Decimal('150.00')
            maximum = Decimal('150.00')
            unit_label = 'photo'
        elif service.slug == 'outdoor-shoot':
            pricing_model = 'per_photo'
            minimum = Decimal('200.00')
            maximum = Decimal('200.00')
            unit_label = 'photo'
        elif service.slug == 'reels-package':
            pricing_model = 'quote_range'
            minimum = Decimal('1000.00')
            maximum = Decimal('80000.00')
            unit_label = 'package'
        else:
            pricing_model = 'quote_range'
            minimum = Decimal('10000.00')
            maximum = Decimal('80000.00')
            unit_label = 'package'

        service.pricing_model = pricing_model
        service.minimum_price = minimum
        service.maximum_price = maximum
        service.unit_label = unit_label
        service.save(update_fields=('pricing_model', 'minimum_price', 'maximum_price', 'unit_label'))


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0004_normalize_legacy_booking_lifecycle'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicetype',
            name='pricing_model',
            field=models.CharField(
                choices=[('per_photo', 'Per photo'), ('quote_range', 'Custom quote within range')],
                default='quote_range',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='servicetype',
            name='minimum_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='servicetype',
            name='maximum_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='servicetype',
            name='unit_label',
            field=models.CharField(default='package', max_length=40),
        ),
        migrations.AddField(
            model_name='booking',
            name='photo_count',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(convert_service_pricing, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='servicetype',
            name='suggested_price',
        ),
    ]