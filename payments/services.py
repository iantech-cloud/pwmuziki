import base64
from datetime import datetime
import json
from urllib.request import Request, urlopen
from django.conf import settings

def _request(url, *, method='GET', headers=None, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, headers=headers or {}, method=method)
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read())

def mpesa_access_token():
    if not all([
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET,
        settings.MPESA_SHORTCODE,
        settings.MPESA_PASSKEY,
        settings.MPESA_CALLBACK_URL,
    ]):
        raise RuntimeError('M-Pesa is not configured yet. Add the provider settings before taking payments.')
    credentials = f'{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}'.encode()
    return _request(settings.MPESA_AUTH_URL, headers={'Authorization': f'Basic {base64.b64encode(credentials).decode()}'})['access_token']

def initiate_stk_push(*, phone_number, amount, account_reference, description):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()).decode()
    payload = {'BusinessShortCode': settings.MPESA_SHORTCODE, 'Password': password, 'Timestamp': timestamp, 'TransactionType': 'CustomerPayBillOnline', 'Amount': int(amount), 'PartyA': phone_number, 'PartyB': settings.MPESA_SHORTCODE, 'PhoneNumber': phone_number, 'CallBackURL': settings.MPESA_CALLBACK_URL, 'AccountReference': account_reference, 'TransactionDesc': description}
    return _request(settings.MPESA_STK_URL, method='POST', payload=payload, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {mpesa_access_token()}'})
