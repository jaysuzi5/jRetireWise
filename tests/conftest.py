"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
import django
from django.conf import settings
from django.contrib.auth.models import User
from factory import Faker


# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


@pytest.fixture
def user_factory():
    """Factory for creating test users."""
    def _create_user(email='test@example.com', username='testuser', **kwargs):
        return User.objects.create_user(
            email=email,
            username=username,
            password='testpass123',
            **kwargs
        )
    return _create_user


@pytest.fixture
def authenticated_user(user_factory):
    """Create an authenticated test user."""
    return user_factory()


@pytest.fixture
def api_client():
    """Return a Django REST Framework API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, authenticated_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=authenticated_user)
    return api_client


@pytest.fixture
def financial_profile(authenticated_user):
    """Create a financial profile for testing."""
    from jretirewise.financial.models import FinancialProfile
    return FinancialProfile.objects.create(
        user=authenticated_user,
        current_age=40,
        retirement_age=65,
        life_expectancy=95,
        annual_spending=60000,
        social_security_annual=30000,
        pension_annual=0,
        current_portfolio_value=1000000,
    )


@pytest.fixture
def asset(authenticated_user):
    """Create a test asset."""
    from jretirewise.financial.models import Asset
    return Asset.objects.create(
        user=authenticated_user,
        name='Main Portfolio',
        asset_type='stock',
        current_value=1000000,
        annual_return_rate=0.07,
        allocation_percentage=60,
    )


@pytest.fixture
def scenario(authenticated_user):
    """Create a test retirement scenario."""
    from jretirewise.scenarios.models import RetirementScenario
    return RetirementScenario.objects.create(
        user=authenticated_user,
        name='Conservative Plan',
        calculator_type='4_percent',
        parameters={
            'annual_return_rate': 0.05,
            'inflation_rate': 0.03,
        }
    )


@pytest.fixture
def db():
    """Enable database access for tests."""
    import pytest_django
    return pytest_django.fixtures.db


# Markers
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow")
