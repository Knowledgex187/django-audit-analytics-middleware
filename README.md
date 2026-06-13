# django-analytics-middleware

**One middleware. Audit logs for compliance. Analytics for product.**

## Status: 🏗️ Building in public

This package is under continuous development. And in production.

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

## Features

- 📊 Logs all HTTP requests with timing data
- 👤 Captures authenticated user UUIDs
- 🌐 Extracts real IP addresses (handles proxies)
- 🚫 Skips configurable noise paths (health checks, admin, etc.)
- 📝 Writes JSON logs for easy parsing
- ⚡ Minimal performance impact
- 🔒 Never breaks your application if logging fails

## Want to help?

- Open an issue with your wishlist
- Star the repo to follow progress
- DM me on LinkedIn

## Installation

```bash
pip install django-analytics-middleware


# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'django_analytics_middleware',
]

# Add to MIDDLEWARE
MIDDLEWARE = [
    ...
    'django_analytics_middleware.middleware.AnalyticsMiddleware',
]

# Configure log path
ANALYTICS_LOG_PATH = os.path.join(BASE_DIR, 'logs', 'analytics.log')

# For .env in settings.py
ANALYTICS_LOG_PATH = ANALYTICS_LOG_PATH=<env_handler>(<LOG PATH>)

Configuration

Required Settings
Setting	Description	Example
ANALYTICS_LOG_PATH	Where to write log files - os.path.join(BASE_DIR, 'logs', 'analytics.log')


Optional Settings
Setting	Default	Description
ANALYTICS_NOISE_PATHS	['/health', '/admin', '/favicon.ico']	Paths to skip logging
ANALYTICS_LOG_LEVEL	'WARNING'	# Logging level for the package


# Example settings.py
# Required
ANALYTICS_LOG_PATH = os.path.join(BASE_DIR, 'logs', 'analytics.log')

# Optional - Custom noise paths
ANALYTICS_NOISE_PATHS = [
    '/health',
    '/metrics', 
    '/admin',
    '/favicon.ico',
    '/robots.txt'
]

# Optional - Set log level (DEBUG, INFO, WARNING, ERROR)
ANALYTICS_LOG_LEVEL = 'INFO'


# Log Format
{
  "path": "/api/users/",
  "method": "GET",
  "status": 200,
  "user_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 45,
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "referrer": "https://example.com/",
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "month": "Jan",
  "week": "03",
  "day": "Mon",
  "hour": "10"
}

# Log Field Descriptions
Field	         Type	    Description
path	         string	    Request URL path
method	         string	    HTTP method (GET, POST, PUT, DELETE, etc.)
status	         integer	HTTP response status code
user_uuid	     string	    Authenticated user's UUID or "unauthorized user"
duration_ms	     integer	Request processing time in milliseconds
ip	string	     Client     IP address (handles proxy forwarding)
user_agent	     string	    Browser/device user agent string
referrer	     string	    Referring URL (where user came from)
timestamp	     string	    ISO 8601 timestamp with timezone
month	         string	    Three-letter month abbreviation (Jan, Feb, Mar)
week	         string	    ISO week number (01-53)
day	             string	    Three-letter day abbreviation (Mon, Tue, Wed)
hour	         string	    Hour in 24-hour format (00-23)

## License

MIT – Because audit logs shouldn't be paywalled.