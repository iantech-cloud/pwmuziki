from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('users', '0002_profile_is_featured')]

    operations = [
        migrations.CreateModel(
            name='ClientNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('status', models.CharField(choices=[('lead', 'Lead'), ('booked', 'Booked'), ('completed', 'Completed'), ('archived', 'Archived')], default='lead', max_length=20)),
                ('tags', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photographer_notes', to=settings.AUTH_USER_MODEL)),
                ('photographer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='StudioSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(blank=True, max_length=160)),
                ('service_area', models.CharField(blank=True, max_length=160)),
                ('default_gallery_expiry_days', models.PositiveIntegerField(default=30)),
                ('default_allow_downloads', models.BooleanField(default=False)),
                ('email_notifications', models.BooleanField(default=True)),
                ('photographer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='studio_settings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_threads', to=settings.AUTH_USER_MODEL)),
                ('photographer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GalleryAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(blank=True, max_length=128)),
                ('allow_downloads', models.BooleanField(default=False)),
                ('allow_favorites', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('album', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client_access', to='portfolio.album')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='galleries', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Photography agreement', max_length=160)),
                ('body', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('sent', 'Sent'), ('signed', 'Signed')], default='draft', max_length=20)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='bookings.booking')),
            ],
        ),
        migrations.CreateModel(
            name='GalleryFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_favorites', to=settings.AUTH_USER_MODEL)),
                ('gallery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='users.galleryaccess')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_favorites', to='portfolio.photo')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='users.messagethread')),
            ],
            options={'ordering': ['created_at']},
        ),
        migrations.AddConstraint(model_name='messagethread', constraint=models.UniqueConstraint(fields=('photographer', 'client'), name='unique_message_thread')),
        migrations.AddConstraint(model_name='galleryfavorite', constraint=models.UniqueConstraint(fields=('gallery', 'photo', 'client'), name='unique_gallery_favorite')),
    ]
