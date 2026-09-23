import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Load shared defaults first, then local overrides. Existing deployment variables
# remain authoritative because python-dotenv does not override os.environ by default.
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR / '.env.local')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    if os.environ.get('DJANGO_DEBUG', '').lower() == 'true':
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise RuntimeError('SESSION_SECRET must be configured when DEBUG is disabled.')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'pwmuziki.vercel.app',
    '.vercel.app',
    '.vercel.run',
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
]
for host_variable in ('REPLIT_DEV_DOMAIN', 'VERCEL_URL'):
    host = os.environ.get(host_variable)
    if host:
        ALLOWED_HOSTS.append(host.split('://', 1)[-1].split('/', 1)[0])

CSRF_TRUSTED_ORIGINS = ['https://pwmuziki.vercel.app']
for origin_variable in ('VERCEL_URL', 'REPLIT_DEV_DOMAIN'):
    origin = os.environ.get(origin_variable)
    if origin:
        origin = origin if origin.startswith('http') else f'https://{origin}'
        CSRF_TRUSTED_ORIGINS.append(origin.rstrip('/'))
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'bookings',
    'portfolio',
    'payments',
    'reviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pwmuziki.urls'
AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pwmuziki.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    parsed_database_url = urlparse(DATABASE_URL)
    database_options = dict(parse_qsl(parsed_database_url.query))
    database_options.setdefault('sslmode', 'require')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_database_url.path.lstrip('/'),
            'USER': parsed_database_url.username,
            'PASSWORD': parsed_database_url.password,
            'HOST': parsed_database_url.hostname,
            'PORT': parsed_database_url.port or 5432,
            'OPTIONS': database_options,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox').lower()
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', '')
MPESA_CALLBACK_TOKEN = os.environ.get('MPESA_CALLBACK_TOKEN', '')
MPESA_AUTH_URL = os.environ.get(
    'MPESA_AUTH_URL',
    'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if MPESA_ENVIRONMENT == 'production'
    else 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
)
MPESA_STK_URL = os.environ.get(
    'MPESA_STK_URL',
    'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if MPESA_ENVIRONMENT == 'production'
    else 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
)
MPESA_TRANSACTION_TYPE = os.environ.get('MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')
MPESA_PARTY_B = os.environ.get('MPESA_PARTY_B', MPESA_SHORTCODE)
MPESA_ACCOUNT_REFERENCE = os.environ.get('MPESA_ACCOUNT_REFERENCE', 'AuraCity')
MPESA_QUERY_URL = os.environ.get(
    'MPESA_QUERY_URL',
    'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    if MPESA_ENVIRONMENT == 'production'
    else 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query',
)
MPESA_B2C_URL = os.environ.get(
    'MPESA_B2C_URL',
    'https://api.safaricom.co.ke/mpesa/b2c/v3/paymentrequest'
    if MPESA_ENVIRONMENT == 'production'
    else 'https://sandbox.safaricom.co.ke/mpesa/b2c/v3/paymentrequest',
)
MPESA_B2C_COMMAND_ID = os.environ.get('MPESA_B2C_COMMAND_ID', 'BusinessPayment')
MPESA_B2C_INITIATOR_NAME = os.environ.get('MPESA_B2C_INITIATOR_NAME', '')
MPESA_B2C_SECURITY_CREDENTIAL = os.environ.get('MPESA_B2C_SECURITY_CREDENTIAL', '')
MPESA_B2C_RESULT_URL = os.environ.get('MPESA_B2C_RESULT_URL', '')
MPESA_B2C_TIMEOUT_URL = os.environ.get('MPESA_B2C_TIMEOUT_URL', '')


# Email
# Gmail SMTP requires a Google App Password, not the account password.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
EMAIL_TIMEOUT = 20
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000').rstrip('/')
BRAND_NAME = 'AuraCity'
