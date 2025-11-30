"""
Apps config for authentication.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jretirewise.authentication'
