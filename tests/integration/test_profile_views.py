"""
Integration tests for profile views and forms.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from jretirewise.financial.models import FinancialProfile


class ProfileViewIntegrationTestCase(TestCase):
    """Test ProfileView with full request/response cycle."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_profile_page_loads(self):
        """Test that profile page loads correctly."""
        response = self.client.get('/profile/')
        assert response.status_code == 200
        assert 'Financial Profile' in response.content.decode()

    def test_profile_page_requires_authentication(self):
        """Test that profile page requires login."""
        client = Client()
        response = client.get('/profile/')
        # Should redirect to login
        assert response.status_code == 302

    def test_create_new_profile(self):
        """Test creating a new financial profile via form submission."""
        profile_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'social_security_annual': '20000.00',
            'pension_annual': '0.00',
            'pension_start_age': 65,
        }
        response = self.client.post('/profile/', profile_data, follow=True)
        assert response.status_code == 200

        # Verify profile was created
        profile = FinancialProfile.objects.get(user=self.user)
        assert profile.current_age == 35
        assert profile.retirement_age == 65
        assert float(profile.annual_spending) == 80000.00

    def test_update_existing_profile(self):
        """Test updating an existing financial profile."""
        # Create initial profile
        profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=30,
            retirement_age=60,
            life_expectancy=90,
            current_portfolio_value=100000,
        )

        # Update profile
        updated_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '90000.00',
            'social_security_annual': '25000.00',
            'pension_annual': '10000.00',
            'pension_start_age': 62,
        }
        response = self.client.post('/profile/', updated_data, follow=True)
        assert response.status_code == 200

        # Verify profile was updated
        profile.refresh_from_db()
        assert profile.current_age == 35
        assert profile.retirement_age == 65
        assert float(profile.annual_spending) == 90000.00
        assert float(profile.pension_annual) == 10000.00
        assert profile.pension_start_age == 62

    def test_profile_form_validation_error(self):
        """Test that validation errors are displayed."""
        invalid_data = {
            'current_age': 70,  # Invalid: greater than retirement age
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'pension_annual': '0.00',
            'pension_start_age': 65,
        }
        response = self.client.post('/profile/', invalid_data)
        assert response.status_code == 200
        # Form should be re-displayed with errors
        content = response.content.decode()
        assert 'Retirement age must be greater than or equal to current age' in content

    def test_profile_required_fields_validation(self):
        """Test that required fields are validated."""
        invalid_data = {
            'retirement_age': 65,
            # Missing current_age and other required fields
        }
        response = self.client.post('/profile/', invalid_data)
        assert response.status_code == 200
        content = response.content.decode()
        # Should show validation errors
        assert 'required' in content.lower() or 'error' in content.lower()

    def test_profile_displays_existing_data(self):
        """Test that existing profile data is displayed in form."""
        profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=45,
            retirement_age=70,
            life_expectancy=100,
            current_portfolio_value=750000,
            annual_spending=120000,
        )

        response = self.client.get('/profile/')
        assert response.status_code == 200
        content = response.content.decode()
        # Check that values are in the form
        assert '45' in content
        assert '70' in content
        assert '100' in content

    def test_profile_success_message(self):
        """Test that success message is displayed after save."""
        profile_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'social_security_annual': '20000.00',
            'pension_annual': '0.00',
            'pension_start_age': 65,
        }
        response = self.client.post('/profile/', profile_data, follow=True)
        assert response.status_code == 200
        # Check for success message
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert 'updated successfully' in str(messages[0]).lower()

    def test_all_profile_fields_required(self):
        """Test that all required fields must be present."""
        required_fields = [
            'current_age',
            'retirement_age',
            'annual_spending',
        ]

        base_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'pension_annual': '0.00',
            'pension_start_age': 65,
        }

        # Test with each required field missing
        for field in required_fields:
            test_data = base_data.copy()
            del test_data[field]
            response = self.client.post('/profile/', test_data)
            assert response.status_code == 200
            # Should re-render with error
            assert field in response.content.decode().lower() or 'error' in response.content.decode().lower()
