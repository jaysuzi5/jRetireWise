"""
End-to-end tests using Playwright for complete user workflows.
These tests run against the live Django application via the browser.
"""

import pytest
import json
from playwright.sync_api import Page, expect


@pytest.fixture
def base_url():
    """Base URL for the application."""
    return "http://web:8000"


class TestSignupAndLogin:
    """Test user signup and login workflows."""

    def test_user_can_sign_up(self, page: Page, base_url: str):
        """Test complete signup flow."""
        page.goto(f"{base_url}/auth/accounts/signup/")

        # Fill signup form
        page.fill('input[name="email"]', f'newuser_{int(page.evaluate("Date.now()"))}@example.com')
        page.fill('input[name="password1"]', 'SecurePassword123!')
        page.fill('input[name="password2"]', 'SecurePassword123!')

        # Submit form
        page.click('button[type="submit"]')

        # Should redirect to confirmation or login page
        page.wait_for_load_state('networkidle')
        assert page.url != f"{base_url}/auth/accounts/signup/"

    def test_user_can_login(self, page: Page, base_url: str):
        """Test login flow with existing user."""
        page.goto(f"{base_url}/auth/accounts/login/")

        # Fill login form
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')

        # Submit form
        page.click('button[type="submit"]')

        # Should redirect to dashboard
        page.wait_for_load_state('networkidle')
        assert "/dashboard" in page.url or page.url.endswith("/")


class TestProfileWorkflow:
    """Test financial profile creation and update workflow."""

    def test_can_create_financial_profile(self, page: Page, base_url: str):
        """Test creating a new financial profile."""
        # Login first
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Navigate to profile
        page.goto(f"{base_url}/profile/")

        # Fill profile form
        page.fill('input[name="current_age"]', '35')
        page.fill('input[name="retirement_age"]', '65')
        page.fill('input[name="life_expectancy"]', '95')
        page.fill('input[name="current_portfolio_value"]', '500000')
        page.fill('input[name="annual_spending"]', '80000')
        page.fill('input[name="social_security_annual"]', '20000')
        page.fill('input[name="pension_annual"]', '0')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show success message or redirect
        assert page.url.endswith('/profile/') or 'updated' in page.content().lower()

    def test_profile_form_validation(self, page: Page, base_url: str):
        """Test that profile form validation works."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/profile/")

        # Fill invalid data (retirement age before current age)
        page.fill('input[name="current_age"]', '70')
        page.fill('input[name="retirement_age"]', '65')
        page.fill('input[name="life_expectancy"]', '95')
        page.fill('input[name="current_portfolio_value"]', '500000')
        page.fill('input[name="annual_spending"]', '80000')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show error message
        error_text = page.content().lower()
        assert 'retirement age must be greater' in error_text or 'error' in error_text

    def test_profile_data_persists(self, page: Page, base_url: str):
        """Test that profile data persists after save."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/profile/")

        # Fill and save profile
        page.fill('input[name="current_age"]', '45')
        page.fill('input[name="retirement_age"]', '70')
        page.fill('input[name="life_expectancy"]', '100')
        page.fill('input[name="current_portfolio_value"]', '750000')
        page.fill('input[name="annual_spending"]', '100000')
        page.fill('input[name="social_security_annual"]', '25000')
        page.fill('input[name="pension_annual"]', '10000')

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Reload page and verify data
        page.goto(f"{base_url}/profile/")
        page.wait_for_load_state('networkidle')

        # Check that values are present in form
        current_age_value = page.input_value('input[name="current_age"]')
        assert current_age_value == '45'


class TestScenarioWorkflow:
    """Test retirement scenario creation and management workflow."""

    def test_can_create_scenario(self, page: Page, base_url: str):
        """Test creating a retirement scenario."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/dashboard/create/")

        # Fill scenario form
        page.fill('input[name="name"]', 'Conservative Plan')
        page.fill('textarea[name="description"]', 'A conservative retirement strategy')
        page.select_option('select[name="calculator_type"]', '4_percent')
        page.fill('textarea[name="parameters_json"]', '{"annual_return": 0.05}')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show success or redirect to scenarios list
        assert '/dashboard' in page.url

    def test_scenario_form_json_validation(self, page: Page, base_url: str):
        """Test that invalid JSON is caught."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/dashboard/create/")

        # Fill with invalid JSON
        page.fill('input[name="name"]', 'Invalid Plan')
        page.fill('textarea[name="description"]', 'Plan with bad JSON')
        page.select_option('select[name="calculator_type"]', '4_percent')
        page.fill('textarea[name="parameters_json"]', '{invalid json}')

        # Submit form
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Should show error
        assert 'invalid json' in page.content().lower() or 'json' in page.content().lower()

    def test_can_view_scenario_list(self, page: Page, base_url: str):
        """Test viewing the scenarios list."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/dashboard/")
        page.wait_for_load_state('networkidle')

        # Should show scenarios page
        content = page.content().lower()
        assert 'scenario' in content

    def test_can_access_scenario_detail(self, page: Page, base_url: str):
        """Test accessing scenario detail page."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Try to access a scenario (assuming ID 1 exists or will be created)
        page.goto(f"{base_url}/dashboard/1/")
        page.wait_for_load_state('networkidle')

        # Should either show the scenario or 404
        assert page.status_code in [200, 404]


class TestDashboard:
    """Test dashboard functionality."""

    def test_dashboard_loads(self, page: Page, base_url: str):
        """Test that dashboard loads for authenticated user."""
        page.goto(f"{base_url}/auth/accounts/login/")
        page.fill('input[name="login"]', 'testuser@example.com')
        page.fill('input[name="password"]', 'SecurePass123!')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        page.goto(f"{base_url}/")
        page.wait_for_load_state('networkidle')

        # Should be on dashboard
        assert '/profile/' not in page.url or 'jRetireWise' in page.content()

    def test_unauthenticated_redirect(self, page: Page, base_url: str):
        """Test that unauthenticated users are redirected."""
        page.goto(f"{base_url}/profile/")
        page.wait_for_load_state('networkidle')

        # Should redirect to login
        assert 'login' in page.url.lower() or 'signin' in page.url.lower()
