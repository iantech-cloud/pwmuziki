from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('payments', '0005_payout_processing_and_receipts')]

    operations = [
        migrations.AddField(model_name='invoice', name='status', field=models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('viewed', 'Viewed'), ('partial', 'Partially paid'), ('paid', 'Paid'), ('overdue', 'Overdue')], default='draft', max_length=20)),
        migrations.AddField(model_name='invoice', name='notes', field=models.TextField(blank=True)),
        migrations.CreateModel(name='InvoiceLineItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('description', models.CharField(max_length=180)), ('quantity', models.PositiveIntegerField(default=1)),
            ('unit_amount', models.DecimalField(decimal_places=2, max_digits=10)),
            ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='line_items', to='payments.invoice')),
        ]),
    ]
