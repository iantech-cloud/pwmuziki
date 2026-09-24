---
name: Protected uploaded media
description: Uploaded portfolio, delivery, and profile files require model-aware authorization instead of generic media serving.
---

Uploaded files must be served through an authorization-aware endpoint rather than a generic static media handler. Public portfolio files may be cacheable; private album and delivery files must require the owning photographer or currently authorized client, respect gallery expiry, and use private no-store caching.

**Why:** A generic `/media/` static route lets anyone who guesses or receives an uploaded file URL bypass the page-level gallery authorization.

**How to apply:** When adding an uploaded-image model or template, register its file field with the protected media authorization logic and add tests for anonymous, unrelated-user, authorized, expired, and public access.