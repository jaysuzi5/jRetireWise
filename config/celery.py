"""
Celery config for jRetireWise project.
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('jretirewise')

# Initialize OpenTelemetry after Celery app is created
# This prevents initialization issues during collectstatic
try:
    from config.otel import initialize_otel
    initialize_otel()
except Exception as e:
    # Don't fail if OTEL initialization fails during app creation
    import sys
    print(f"Warning: Failed to initialize OpenTelemetry: {e}", file=sys.stderr)

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat schedules (for Phase 2+)
app.conf.beat_schedule = {
    # Future scheduled tasks
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
