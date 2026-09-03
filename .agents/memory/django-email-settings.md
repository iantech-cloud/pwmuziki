---
name: Django 6.1 email settings
description: Compatibility note for the imported Django 6.1 project email configuration.
---

Django 6.1 rejects defining legacy `EMAIL_BACKEND` alongside the new `MAILERS` setting. Keep the console email backend inside `MAILERS` when using the Django 6.1 settings format.

**Why:** The framework raises `ImproperlyConfigured` during settings initialization when both configuration styles are present.

**How to apply:** When adding password reset or other email flows, update the existing `MAILERS` mapping rather than adding `EMAIL_BACKEND`.