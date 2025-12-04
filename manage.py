#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    # Initialize OpenTelemetry for management commands (e.g., migrate, createsuperuser)
    try:
        from config.otel import initialize_otel
        initialize_otel()
    except Exception as e:
        # Don't fail if OpenTelemetry initialization fails
        print(f"Warning: Failed to initialize OpenTelemetry: {e}")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
