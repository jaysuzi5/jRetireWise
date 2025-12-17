"""
Unit tests for form validation.
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.financial.forms import FinancialProfileForm, AssetForm
from jretirewise.financial.models import FinancialProfile
from jretirewise.scenarios.forms import ScenarioForm


class FinancialProfileFormTestCase(TestCase):
    """Test FinancialProfileForm validation and saving."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def test_valid_profile_form(self):
        """Test form with valid data."""
        form_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'social_security_annual': '20000.00',
            'pension_annual': '0.00',
        }
        form = FinancialProfileForm(data=form_data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_profile_form_saves_correctly(self):
        """Test that form saves all FinancialProfile fields correctly."""
        form_data = {
            'current_age': 40,
            'retirement_age': 67,
            'life_expectancy': 90,
            'annual_spending': '100000.00',
            'pension_annual': '15000.00',
            'pension_start_age': 62,
        }
        form = FinancialProfileForm(data=form_data)
        assert form.is_valid()

        profile = form.save(commit=False)
        profile.user = self.user
        profile.save()

        # Verify all financial profile fields were saved
        saved_profile = FinancialProfile.objects.get(user=self.user)
        assert saved_profile.current_age == 40
        assert saved_profile.retirement_age == 67
        assert saved_profile.life_expectancy == 90
        assert float(saved_profile.annual_spending) == 100000.00
        assert float(saved_profile.pension_annual) == 15000.00
        assert saved_profile.pension_start_age == 62

    def test_profile_form_age_validation(self):
        """Test that current_age must be less than retirement_age."""
        form_data = {
            'current_age': 70,  # Invalid: greater than retirement age
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'social_security_annual': '0.00',
            'pension_annual': '0.00',
        }
        form = FinancialProfileForm(data=form_data)
        assert not form.is_valid()
        assert 'Retirement age must be greater than or equal to current age' in str(form.errors)

    def test_profile_form_life_expectancy_validation(self):
        """Test that life_expectancy must be greater than retirement_age."""
        form_data = {
            'current_age': 35,
            'retirement_age': 65,
            'life_expectancy': 60,  # Invalid: less than retirement age
            'annual_spending': '80000.00',
            'social_security_annual': '0.00',
            'pension_annual': '0.00',
        }
        form = FinancialProfileForm(data=form_data)
        assert not form.is_valid()
        assert 'Life expectancy must be greater than retirement age' in str(form.errors)

    def test_profile_form_required_fields(self):
        """Test that required fields are enforced."""
        form_data = {
            'retirement_age': 65,
            'life_expectancy': 95,
            # Missing current_age
        }
        form = FinancialProfileForm(data=form_data)
        assert not form.is_valid()
        assert 'current_age' in form.errors

    def test_profile_form_minimum_age(self):
        """Test that ages must be at least 18."""
        form_data = {
            'current_age': 10,  # Invalid: less than 18
            'retirement_age': 65,
            'life_expectancy': 95,
            'annual_spending': '80000.00',
            'social_security_annual': '0.00',
            'pension_annual': '0.00',
        }
        form = FinancialProfileForm(data=form_data)
        assert not form.is_valid()


class ScenarioFormTestCase(TestCase):
    """Test ScenarioForm validation and saving."""

    def test_valid_scenario_form(self):
        """Test form with valid data."""
        form_data = {
            'name': 'Conservative Plan',
            'description': 'A conservative retirement plan',
            'calculator_type': '4_percent',
            'parameters_json': '{"annual_return": 0.05, "inflation_rate": 0.03}',
        }
        form = ScenarioForm(data=form_data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_scenario_form_empty_parameters(self):
        """Test form with empty parameters (optional)."""
        form_data = {
            'name': 'Basic Plan',
            'description': 'A basic plan',
            'calculator_type': '4_7_percent',
            'parameters_json': '',
        }
        form = ScenarioForm(data=form_data)
        assert form.is_valid()

    def test_scenario_form_invalid_json(self):
        """Test form with invalid JSON parameters."""
        form_data = {
            'name': 'Invalid Plan',
            'description': 'Plan with bad JSON',
            'calculator_type': '4_percent',
            'parameters_json': '{"invalid json}',  # Bad JSON
        }
        form = ScenarioForm(data=form_data)
        assert not form.is_valid()
        assert 'Invalid JSON' in str(form.errors['parameters_json'])

    def test_scenario_form_required_fields(self):
        """Test that required fields are enforced."""
        form_data = {
            'description': 'Missing name and type',
            # Missing name and calculator_type
        }
        form = ScenarioForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'calculator_type' in form.errors

    def test_scenario_form_all_calculator_types(self):
        """Test form with all calculator type options."""
        calculator_types = ['4_percent', '4_7_percent', 'monte_carlo', 'historical']
        for calc_type in calculator_types:
            form_data = {
                'name': f'Test {calc_type}',
                'description': f'Testing {calc_type}',
                'calculator_type': calc_type,
                'parameters_json': '',
            }
            form = ScenarioForm(data=form_data)
            assert form.is_valid(), f"Form invalid for {calc_type}: {form.errors}"
