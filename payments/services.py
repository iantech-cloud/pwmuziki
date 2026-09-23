import base64
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo
from django.conf import settings

def _request(url, *, method='GET', headers=None, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read()
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise RuntimeError('Daraja returned an invalid JSON response.') from exc
    except HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get('errorMessage', '')
        except (json.JSONDecodeError, AttributeError):
            detail = ''
        suffix = f' {detail}' if detail else ''
        raise RuntimeError(f'Daraja returned HTTP {exc.code}.{suffix}') from exc
    except URLError as exc:
        raise RuntimeError(f'Could not reach Daraja: {exc.reason}') from exc

def mpesa_access_token():
    if not all([
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET,
    ]):
        raise RuntimeError('Daraja is not configured yet. Add MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET.')
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
    try:
        amount = Decimal(str(amount)).quantize(Decimal('1'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError('Payment amount must be a valid number.') from exc
    if amount <= 0:
        raise ValueError('Payment amount must be greater than zero.')
    if not all((settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY)):
        raise RuntimeError('STK Push is not configured yet. Add MPESA_SHORTCODE and MPESA_PASSKEY.')
    timestamp = datetime.now(ZoneInfo('Africa/Nairobi')).strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()).decode()
    callback_url = settings.MPESA_CALLBACK_URL
    if settings.MPESA_CALLBACK_TOKEN:
        parts = urlsplit(callback_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query['token'] = settings.MPESA_CALLBACK_TOKEN
        callback_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': settings.MPESA_TRANSACTION_TYPE,
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': settings.MPESA_PARTY_B,
        'PhoneNumber': phone_number,
        'CallBackURL': callback_url,
        'AccountReference': account_reference or settings.MPESA_ACCOUNT_REFERENCE,
        'TransactionDesc': description,
    }
    return _request(settings.MPESA_STK_URL, method='POST', payload=payload, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mpesa_access_token()}'})


def query_stk_push(*, checkout_request_id):
    if not checkout_request_id:
        raise ValueError('A checkout request ID is required.')
    if not all((settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY)):
        raise RuntimeError('STK Push query is not configured yet. Add MPESA_SHORTCODE and MPESA_PASSKEY.')
    timestamp = datetime.now(ZoneInfo('Africa/Nairobi')).strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()
    ).decode()
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    return _request(
        settings.MPESA_QUERY_URL,
        method='POST',
        payload=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mpesa_access_token()}'},
    )


def initiate_b2c_payout(*, phone_number, amount, remarks, occasion):
    phone_number = normalize_phone_number(phone_number)
    required = (
        settings.MPESA_B2C_INITIATOR_NAME,
        settings.MPESA_B2C_SECURITY_CREDENTIAL,
        settings.MPESA_B2C_RESULT_URL,
        settings.MPESA_B2C_TIMEOUT_URL,
    )
    if not all(required):
        raise RuntimeError(
            'B2C payouts are not configured. Add MPESA_B2C_INITIATOR_NAME, '
            'MPESA_B2C_SECURITY_CREDENTIAL, MPESA_B2C_RESULT_URL, and MPESA_B2C_TIMEOUT_URL.'
        )
    if amount <= 0:
        raise ValueError('Payout amount must be greater than zero.')
    payload = {
        'InitiatorName': settings.MPESA_B2C_INITIATOR_NAME,
        'SecurityCredential': settings.MPESA_B2C_SECURITY_CREDENTIAL,
        'CommandID': settings.MPESA_B2C_COMMAND_ID,
        'Amount': int(amount),
        'PartyA': settings.MPESA_SHORTCODE,
        'PartyB': phone_number,
        'Remarks': remarks,
        'QueueTimeOutURL': settings.MPESA_B2C_TIMEOUT_URL,
        'ResultURL': settings.MPESA_B2C_RESULT_URL,
        'Occasion': occasion,
    }
    return _request(
        settings.MPESA_B2C_URL,
        method='POST',
        payload=payload,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mpesa_access_token()}'},
    )
