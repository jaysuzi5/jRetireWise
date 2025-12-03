"""
Apps config for scenarios app.
"""

from django.apps import AppConfig


class ScenariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jretirewise.scenarios'

    def ready(self):
        """Register signal handlers."""
        import jretirewise.scenarios.signals  # noqa
