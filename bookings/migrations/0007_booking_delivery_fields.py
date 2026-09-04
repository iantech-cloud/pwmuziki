from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0006_remove_legacy_deposit_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='delivery_note',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='delivery_ready_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='google_drive_url',
            field=models.URLField(blank=True),
        ),
    ]