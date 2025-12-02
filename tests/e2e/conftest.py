"""
Configuration and fixtures for E2E tests.
"""

import os
import pytest
from playwright.sync_api import sync_playwright, Page
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture(scope="session")
def base_url():
    """Get base URL from environment or use default.

    This is a session-scoped fixture to work with pytest-base-url plugin.
    It can be overridden with the --base-url command-line option.
    """
    return os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the entire test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """Create a new page for each test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    """Ensure Django database is set up for tests."""
    from django import setup
    from django.conf import settings

    if not settings.configured:
        setup()


@pytest.fixture(autouse=True)
def create_test_user():
    """Create a test user for E2E tests."""
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@example.com',
        }
    )
    if created:
        user.set_password('SecurePass123!')
        user.save()
    return user
