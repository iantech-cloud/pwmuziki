from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0007_booking_delivery_fields'),
        ('portfolio', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='branded_image',
            field=models.ImageField(blank=True, upload_to='portfolio/branded/'),
        ),
        migrations.AddField(
            model_name='photo',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Include this branded photograph in the public gallery.'),
        ),
        migrations.CreateModel(
            name='DeliveryPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='deliveries/previews/')),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_photos', to='bookings.booking')),
            ],
        ),
    ]