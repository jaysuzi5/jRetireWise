"""
Management command to initialize Google OAuth provider for django-allauth.

This command creates or updates the SocialApp entry for Google OAuth2 authentication.
It should be run after migrations during application initialization.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Initialize Google OAuth provider for django-allauth'

    def handle(self, *args, **options):
        # Get credentials from environment
        client_id = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '').strip()
        client_secret = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '').strip()

        # Validate credentials are not placeholder values
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.WARNING(
                    'Google OAuth credentials not set. Google login will not work. '
                    'Set SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET.'
                )
            )
            return

        if client_id.startswith('your-') or client_secret.startswith('your-'):
            self.stdout.write(
                self.style.WARNING(
                    'Google OAuth credentials are placeholder values. '
                    'Update SOCIAL_AUTH_GOOGLE_OAUTH2_KEY and SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET '
                    'with real Google OAuth credentials.'
                )
            )

        # Get or create Site
        site = Site.objects.get_or_create(
            pk=1,
            defaults={'domain': 'jretirewise.jaycurtis.org', 'name': 'jRetireWise'}
        )[0]

        # Create or update Google SocialApp
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth2',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if created:
            app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Google OAuth SocialApp created for site: {site.domain}')
            )
        else:
            # Update credentials if they've changed
            if app.client_id != client_id or app.secret != client_secret:
                app.client_id = client_id
                app.secret = client_secret
                app.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Google OAuth SocialApp credentials updated')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Google OAuth SocialApp already configured')
                )

            # Ensure site is linked
            if site not in app.sites.all():
                app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Linked SocialApp to site: {site.domain}')
                )
