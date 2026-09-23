from django.conf import settings

# Keep provider configuration isolated from the core payments domain.
MPESA_AUTH_URL = getattr(settings, 'MPESA_AUTH_URL', 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials')
MPESA_STK_URL = getattr(settings, 'MPESA_STK_URL', 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest')
