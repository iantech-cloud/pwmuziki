from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0004_invoice_balance_amount_invoice_balance_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payout',
            name='failure_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='payout',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payout',
            name='raw_response',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='payout',
            name='requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payout',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='receipt_number',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]