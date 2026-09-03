import base64
from datetime import datetime
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from django.conf import settings

def _request(url, *, method='GET', headers=None, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Daraja returned HTTP {exc.code}: {body[:240]}') from exc
    except URLError as exc:
        raise RuntimeError(f'Could not reach Daraja: {exc.reason}') from exc

def mpesa_access_token():
    if not all([
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET,
        settings.MPESA_SHORTCODE,
        settings.MPESA_PASSKEY,
    ]):
        raise RuntimeError('Daraja is not configured yet. Add MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE, and MPESA_PASSKEY.')
    credentials = f'{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}'.encode()
    return _request(settings.MPESA_AUTH_URL, headers={'Authorization': f'Basic {base64.b64encode(credentials).decode()}'})['access_token']


def normalize_phone_number(phone_number):
    digits = re.sub(r'\D', '', phone_number or '')
    if digits.startswith('0'):
        digits = f'254{digits[1:]}'
    elif digits.startswith('7') or digits.startswith('1'):
        digits = f'254{digits}'
    if not re.fullmatch(r'254[17]\d{8}', digits):
        raise ValueError('Enter a valid Kenyan M-Pesa number, for example 0712345678 or +254712345678.')
    return digits


def initiate_stk_push(*, phone_number, amount, account_reference, description):
    phone_number = normalize_phone_number(phone_number)
    if not settings.MPESA_CALLBACK_URL:
        raise RuntimeError('Daraja callback is not configured. Set MPESA_CALLBACK_URL to a public HTTPS endpoint.')
    if amount <= 0:
        raise ValueError('Payment amount must be greater than zero.')
    timestamp = datetime.now(ZoneInfo('Africa/Nairobi')).strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()).decode()
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': settings.MPESA_TRANSACTION_TYPE,
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': settings.MPESA_PARTY_B,
        'PhoneNumber': phone_number,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': account_reference or settings.MPESA_ACCOUNT_REFERENCE,
        'TransactionDesc': description,
    }
    return _request(settings.MPESA_STK_URL, method='POST', payload=payload, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mpesa_access_token()}'})
