from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0006_invoice_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='callback_received_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='checkout_request_id',
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.AddField(
            model_name='transaction',
            name='merchant_request_id',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='transaction',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='result_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='result_description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]