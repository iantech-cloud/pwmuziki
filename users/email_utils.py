import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_branded_email(*, subject, recipient, template, context=None, text_body=None):
    if not recipient:
        return False
    context = {**(context or {}), 'site_url': settings.SITE_URL, 'brand_name': settings.BRAND_NAME}
    html_body = render_to_string(f'emails/{template}.html', context)
    message = EmailMultiAlternatives(subject, text_body or subject, settings.DEFAULT_FROM_EMAIL, [recipient])
    message.attach_alternative(html_body, 'text/html')
    try:
        message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Could not send email template %s to %s', template, recipient)
        return False


def send_welcome_email(user):
    return send_branded_email(
        subject='Welcome to AuraCity',
        recipient=user.email,
        template='welcome',
        context={'user': user},
        text_body=f'Welcome to AuraCity, {user.get_short_name() or user.username}. Find photography that feels like you at {settings.SITE_URL}.',
    )
