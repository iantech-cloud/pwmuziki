# AuraCity

AuraCity is a Django photography marketplace for Nairobi and beyond. Clients can discover photographers, request bookings, follow payment stages, and access delivered galleries. Photographers can manage profiles, portfolios, availability, bookings, and delivery previews.

## Run in Replit

The `Start application` workflow runs:

```bash
DJANGO_DEBUG=True python manage.py runserver 0.0.0.0:5000
```

The project uses SQLite by default for local development and PostgreSQL when `DATABASE_URL` is provided. Run migrations after a fresh checkout:

```bash
python manage.py migrate
```

To create safe local demo accounts, starter services, and public photographer profiles:

```bash
python manage.py seed_demo_users
```

The M-Pesa and SMTP flows require their own environment configuration from `.env.example`; no integration credentials are included in the project.