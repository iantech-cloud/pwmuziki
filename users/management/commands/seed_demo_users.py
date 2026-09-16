from django.core.management.base import BaseCommand
from users.models import Profile, User


class Command(BaseCommand):
    help = 'Create or update the two safe Pwmuziki demo accounts.'

    DEMO_USERS = (
        {
            'username': 'demo-client',
            'email': 'demo.client@pwmuziki.test',
            'first_name': 'Demo',
            'last_name': 'Client',
            'role': User.Role.CLIENT,
            'password': 'PwmuzikiDemoClient2026!',
        },
        {
            'username': 'demo-photographer',
            'email': 'demo.photographer@pwmuziki.test',
            'first_name': 'Demo',
            'last_name': 'Photographer',
            'role': User.Role.PHOTOGRAPHER,
            'password': 'PwmuzikiDemoPhotographer2026!',
        },
    )

    def handle(self, *args, **options):
        for data in self.DEMO_USERS:
            password = data.pop('password')
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={**data, 'is_active': True},
            )
            changed = False
            for field, value in data.items():
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if created or not user.check_password(password):
                user.set_password(password)
                changed = True
            if changed:
                user.save()
            Profile.ensure_for(user)
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} {user.email} ({user.role})'))
