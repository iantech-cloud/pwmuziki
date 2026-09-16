from django.db import migrations


def hash_existing_passwords(apps, schema_editor):
    from django.contrib.auth.hashers import make_password

    GalleryAccess = apps.get_model('users', 'GalleryAccess')
    for gallery in GalleryAccess.objects.exclude(password='').iterator():
        if not gallery.password.startswith(('pbkdf2_', 'argon2$', 'bcrypt$', 'scrypt$')):
            gallery.password = make_password(gallery.password)
            gallery.save(update_fields=['password'])


class Migration(migrations.Migration):
    dependencies = [('users', '0004_notifications_gallery_options')]

    operations = [migrations.RunPython(hash_existing_passwords, migrations.RunPython.noop)]
