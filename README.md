# django-audit-analytics-middleware

**One middleware. Audit logs for compliance. Analytics for product.**

## Status: 🏗️ Building in public

This package is under active development. I'm posting every step on LinkedIn.

## What it will do (already working locally)

- [x] Log every request (path, method, status, user, IP, user agent)
- [x] Filter noise paths (/admin, /health, /static)
- [x] Duration tracking in milliseconds
- [x] IP extraction behind proxies (X-Forwarded-For)
- [ ] Configurable log file path
- [ ] Django admin view for logs
- [ ] Export to CSV/JSON command
- [ ] Tests (coming this week)
- [ ] PyPI release

## Want to help?

- Open an issue with your wishlist
- Star the repo to follow progress
- DM me on LinkedIn

## License

MIT – because audit logs shouldn't be paywalled.
