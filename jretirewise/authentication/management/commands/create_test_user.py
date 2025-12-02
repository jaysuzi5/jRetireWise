"""
Django management command to create test users for E2E testing.

Usage:
    python manage.py create_test_user --email test@example.com --password MyPassword123

For deployment with environment variables:
    python manage.py create_test_user

Environment variables (optional):
    SMOKE_TEST_USER_EMAIL: Test user email (default: smoketest@jretirewise.local)
    SMOKE_TEST_USER_PASSWORD: Test user password (default: SmokeTest123!@#)
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create a test user for E2E smoke tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email for test user (default: from SMOKE_TEST_USER_EMAIL env var)"
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Password for test user (default: from SMOKE_TEST_USER_PASSWORD env var)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and recreate user if it already exists"
        )

    def handle(self, *args, **options):
        # Get email from arguments or environment
        email = options.get("email") or os.environ.get(
            "SMOKE_TEST_USER_EMAIL",
            "smoketest@jretirewise.local"
        )

        # Get password from arguments or environment
        password = options.get("password") or os.environ.get(
            "SMOKE_TEST_USER_PASSWORD",
            "SmokeTest123!@#"
        )

        # Validate inputs
        if not email:
            raise CommandError("Email is required. Set via --email or SMOKE_TEST_USER_EMAIL env var")
        if not password:
            raise CommandError("Password is required. Set via --password or SMOKE_TEST_USER_PASSWORD env var")

        # Extract username from email (part before @)
        username = email.split("@")[0]

        try:
            # Check if user exists
            user = User.objects.filter(email=email).first()

            if user:
                if options.get("force"):
                    # Delete and recreate
                    self.stdout.write(
                        self.style.WARNING(f"Deleting existing user: {email}")
                    )
                    user.delete()
                    user = None
                else:
                    # User exists, just update password
                    self.stdout.write(
                        self.style.WARNING(f"User already exists: {email}")
                    )
                    user.set_password(password)
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated password for: {email}")
                    )
                    return

            # Create new user
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name="Smoke",
                    last_name="Test",
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(f"Created test user: {email}")
                )
                self.stdout.write(f"Username: {username}")
                self.stdout.write(f"Password: {'*' * len(password)}")
                self.stdout.write(
                    self.style.WARNING(
                        "Note: Save these credentials securely (e.g., as GitHub Secrets)"
                    )
                )

        except Exception as e:
            raise CommandError(f"Failed to create test user: {str(e)}")
