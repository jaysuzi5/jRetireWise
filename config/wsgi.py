"""
WSGI config for jRetireWise project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize OpenTelemetry before creating the WSGI application
from config.otel import setup_opentelemetry
setup_opentelemetry()

application = get_wsgi_application()
