from django.core.management.base import BaseCommand
from bookings.models import ServiceType
from portfolio.models import Album, Category
from users.models import Profile, User


class Command(BaseCommand):
    help = 'Create or update safe AuraCity demo accounts and starter marketplace content.'

    DEMO_USERS = (
        {
            'username': 'demo-client',
            'email': 'demo.client@auracity.test',
            'first_name': 'Demo',
            'last_name': 'Client',
            'role': User.Role.CLIENT,
            'password': 'AuraCityDemoClient2026!',
        },
        {
            'username': 'demo-photographer',
            'email': 'demo.photographer@auracity.test',
            'first_name': 'Maya',
            'last_name': 'Njeri',
            'role': User.Role.PHOTOGRAPHER,
            'password': 'AuraCityDemoPhotographer2026!',
            'bio': 'Documentary portraits and event photography.',
            'is_featured': True,
        },
        {
            'username': 'demo-studio',
            'email': 'demo.studio@auracity.test',
            'first_name': 'The',
            'last_name': 'Still Studio',
            'role': User.Role.PHOTOGRAPHER,
            'password': 'AuraCityDemoStudio2026!',
            'bio': 'Portraits and commercial photography for businesses and teams.',
            'is_featured': True,
        },
        {
            'username': 'demo-atelier',
            'email': 'demo.atelier@auracity.test',
            'first_name': 'Asha',
            'last_name': 'Mwangi',
            'role': User.Role.PHOTOGRAPHER,
            'password': 'AuraCityDemoAtelier2026!',
            'bio': 'Wedding and event photography for private and corporate clients.',
        },
    )

    def handle(self, *args, **options):
        for data in self.DEMO_USERS:
            data = data.copy()
            password = data.pop('password')
            bio = data.pop('bio', '')
            is_featured = data.pop('is_featured', False)
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
            profile = Profile.ensure_for(user)
            if bio or profile.bio != bio or profile.is_featured != is_featured:
                profile.bio = bio
                profile.is_featured = is_featured
                profile.save(update_fields=['bio', 'is_featured'])
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} {user.email} ({user.role})'))

        for service in (
            {
                'name': 'Portrait sessions',
                'slug': 'portrait-sessions',
                'description': 'Portrait sessions for individuals, couples, and teams.',
                'pricing_model': ServiceType.PricingModel.QUOTE_RANGE,
                'minimum_price': 18000,
                'maximum_price': 35000,
                'unit_label': 'session',
                'sort_order': 1,
            },
            {
                'name': 'Weddings & celebrations',
                'slug': 'weddings-celebrations',
                'description': 'Full-day photography coverage for weddings and events.',
                'pricing_model': ServiceType.PricingModel.QUOTE_RANGE,
                'minimum_price': 65000,
                'maximum_price': 180000,
                'unit_label': 'event',
                'sort_order': 2,
            },
            {
                'name': 'Commercial photography',
                'slug': 'brand-stories',
                'description': 'Photography for businesses, products, spaces, and teams.',
                'pricing_model': ServiceType.PricingModel.QUOTE_RANGE,
                'minimum_price': 30000,
                'maximum_price': 90000,
                'unit_label': 'project',
                'sort_order': 3,
            },
        ):
            ServiceType.objects.update_or_create(slug=service['slug'], defaults=service)

        category_data = (
            ('Portraits', 'portraits', 'demo-photographer', 'Portrait portfolio'),
            ('Celebrations', 'celebrations', 'demo-atelier', 'Wedding and event portfolio'),
            ('Commercial', 'brand-stories', 'demo-studio', 'Commercial portfolio'),
        )
        legacy_album_titles = {
            'Portrait portfolio': 'The quiet between moments',
            'Wedding and event portfolio': 'A day held in light',
            'Commercial portfolio': 'Objects with a point of view',
        }
        for category_name, category_slug, username, album_title in category_data:
            category, _ = Category.objects.update_or_create(
                slug=category_slug,
                defaults={'name': category_name},
            )
            photographer = User.objects.get(username=username)
            album = Album.objects.filter(
                photographer=photographer,
                title=legacy_album_titles[album_title],
            ).first()
            if album:
                album.title = album_title
                album.category = category
                album.description = 'Published portfolio work from this photographer.'
                album.is_public = True
                album.save(update_fields=['title', 'category', 'description', 'is_public'])
            else:
                Album.objects.update_or_create(
                    photographer=photographer,
                    title=album_title,
                    defaults={
                        'category': category,
                        'description': 'Published portfolio work from this photographer.',
                        'is_public': True,
                    },
                )
        self.stdout.write(self.style.SUCCESS('Starter services and public profiles are ready.'))
