from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('users', '0003_dashboard_entities')]

    operations = [
        migrations.AddField(model_name='galleryaccess', name='download_mode', field=models.CharField(choices=[('none', 'No downloads'), ('web', 'Web size'), ('full', 'Full resolution')], default='none', max_length=10)),
        migrations.AddField(model_name='galleryaccess', name='show_favorites', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='galleryaccess', name='watermark_enabled', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='galleryaccess', name='is_published', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='galleryaccess', name='published_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(name='Notification', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('title', models.CharField(max_length=160)), ('body', models.CharField(blank=True, max_length=255)),
            ('link', models.CharField(blank=True, max_length=255)), ('kind', models.CharField(default='general', max_length=40)),
            ('is_read', models.BooleanField(default=False)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='users.user')),
        ], options={'ordering': ['-created_at']}),
        migrations.CreateModel(name='NotificationPreference', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('email_enabled', models.BooleanField(default=True)), ('gallery_updates', models.BooleanField(default=True)),
            ('booking_updates', models.BooleanField(default=True)), ('payment_updates', models.BooleanField(default=True)),
            ('message_updates', models.BooleanField(default=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to='users.user')),
        ]),
    ]
