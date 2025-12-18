"""
Integration tests for Sensitivity Analysis API endpoints.

Tests the full request/response cycle for all sensitivity analysis endpoints
including parameter adjustment calculations, tornado chart generation, and
saved analysis management.
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from jretirewise.scenarios.models import RetirementScenario, CalculationResult, SensitivityAnalysis
from jretirewise.financial.models import FinancialProfile


class SensitivityAnalysisAPITestCase(TestCase):
    """Integration tests for sensitivity analysis API endpoints."""

    def setUp(self):
        """Set up test user, financial profile, and scenario."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        # Create financial profile
        self.financial_profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=Decimal('60.00'),
            retirement_age=Decimal('65.00'),
            life_expectancy=95,
            current_portfolio_value=Decimal('1000000.00'),
            annual_spending=Decimal('40000.00'),
            social_security_annual=Decimal('0.00'),
            pension_annual=Decimal('0.00'),
            pension_start_age=65
        )

        # Create scenario with 4% calculator
        self.scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test 4% Scenario',
            description='Test scenario for sensitivity analysis',
            calculator_type='4_percent',
            parameters={
                'portfolio_value': 1000000,
                'annual_spending': 40000,
                'current_age': 60,
                'retirement_age': 65,
                'life_expectancy': 95,
                'annual_return_rate': 0.07,
                'inflation_rate': 0.03,
                'social_security_annual': 0,
                'social_security_start_age': 67,
                'pension_annual': 0,
                'pension_start_age': 65,
            }
        )

        # Get calculation result (created automatically by signal)
        self.result = self.scenario.result
        # Update result to be completed with data
        self.result.status = 'completed'
        self.result.result_data = {
            'calculation': {
                'success_rate': 100.0,
                'projections': [
                    {'portfolio_value': 1000000, 'annual_withdrawal': 40000},
                    {'portfolio_value': 950000, 'annual_withdrawal': 40000},
                ]
            }
        }
        self.result.execution_time_ms = 100
        self.result.save()

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.api_url = f'/api/v1/scenarios/{self.scenario.id}/sensitivity'

    def test_calculate_endpoint_requires_authentication(self):
        """Test that calculate endpoint requires authentication."""
        client = APIClient()
        url = f'{self.api_url}/calculate/'
        response = client.post(url, {})
        # DRF returns 403 Forbidden for unauthenticated requests
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_calculate_with_zero_adjustments(self):
        """Test calculate endpoint with no parameter adjustments."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': 0.0,
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert 'success_rate' in result
        assert 'final_value' in result
        assert 'comparison_to_baseline' in result
        assert 'parameters_used' in result
        assert result['success_rate'] >= 0

    def test_calculate_with_return_adjustment(self):
        """Test calculate endpoint with return rate adjustment."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': -0.02,  # -2%
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert result['adjustments']['return_adjustment'] == -0.02
        assert result['parameters_used']['annual_return_rate'] == 0.05  # 7% - 2%

    def test_calculate_with_spending_adjustment(self):
        """Test calculate endpoint with spending adjustment."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': 0.0,
            'spending_adjustment': 0.20,  # +20%
            'inflation_adjustment': 0.0
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert result['adjustments']['spending_adjustment'] == 0.20
        assert result['parameters_used']['annual_spending'] == 48000.0  # 40000 * 1.20

    def test_calculate_with_inflation_adjustment(self):
        """Test calculate endpoint with inflation adjustment."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': 0.0,
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.01  # +1%
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert result['adjustments']['inflation_adjustment'] == 0.01
        assert result['parameters_used']['inflation_rate'] == 0.04  # 3% + 1%

    def test_calculate_with_multiple_adjustments(self):
        """Test calculate endpoint with combined adjustments."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': -0.02,
            'spending_adjustment': 0.10,
            'inflation_adjustment': 0.01
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert result['adjustments']['return_adjustment'] == -0.02
        assert result['adjustments']['spending_adjustment'] == 0.10
        assert result['adjustments']['inflation_adjustment'] == 0.01
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] >= 0

    def test_calculate_invalid_data(self):
        """Test calculate endpoint with invalid data."""
        url = f'{self.api_url}/calculate/'
        data = {
            'return_adjustment': 'invalid',  # Should be float
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_calculate_scenario_without_result(self):
        """Test calculate endpoint fails for scenario with pending result."""
        # Create scenario with pending result (not completed)
        scenario_no_result = RetirementScenario.objects.create(
            user=self.user,
            name='No Result Scenario',
            calculator_type='4_percent',
            parameters={}
        )
        # Result is created automatically by signal but in pending status
        # Update it to ensure it's pending
        result = scenario_no_result.result
        result.status = 'pending'
        result.save()

        url = f'/api/v1/scenarios/{scenario_no_result.id}/sensitivity/calculate/'
        data = {'return_adjustment': 0.0, 'spending_adjustment': 0.0, 'inflation_adjustment': 0.0}

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_tornado_chart_generation(self):
        """Test tornado chart generation endpoint."""
        url = f'{self.api_url}/tornado/'
        data = {}  # Use default ranges

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert 'tornado_data' in result
        assert 'parameter_impacts' in result
        assert len(result['tornado_data']) == 3  # Return, Spending, Inflation

        # Verify tornado data structure
        for item in result['tornado_data']:
            assert 'parameter' in item
            assert 'low_value' in item
            assert 'high_value' in item
            assert 'impact' in item
            assert 'impact_percent' in item
            assert 'range_tested' in item

    def test_tornado_chart_with_custom_ranges(self):
        """Test tornado chart with custom parameter ranges."""
        url = f'{self.api_url}/tornado/'
        data = {
            'return_range_min': -0.03,
            'return_range_max': 0.03,
            'return_step': 0.01,
            'spending_range_min': 0.0,
            'spending_range_max': 0.30,
            'spending_step': 0.10,
            'inflation_range_min': 0.0,
            'inflation_range_max': 0.02,
            'inflation_step': 0.01
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        result = response.json()
        assert len(result['tornado_data']) == 3

        # Verify custom ranges were used
        return_item = next(item for item in result['tornado_data'] if item['parameter'] == 'Return Rate')
        assert return_item['range_tested']['min'] == -0.03
        assert return_item['range_tested']['max'] == 0.03

    def test_tornado_chart_data_sorted_by_impact(self):
        """Test that tornado data is sorted by impact (highest first)."""
        url = f'{self.api_url}/tornado/'
        response = self.client.post(url, {}, format='json')

        result = response.json()
        impacts = [item['impact'] for item in result['tornado_data']]
        assert impacts == sorted(impacts, reverse=True), "Tornado data should be sorted by impact"

    def test_save_sensitivity_analysis(self):
        """Test saving a sensitivity analysis."""
        url = f'{self.api_url}/save/'
        data = {
            'name': 'Conservative Scenario',
            'description': 'Testing with conservative assumptions',
            'return_adjustment': -0.02,
            'spending_adjustment': 0.10,
            'inflation_adjustment': 0.01,
            'result_data': {
                'success_rate': 95.0,
                'final_value': 850000
            }
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Verify sensitivity analysis was saved
        analysis = SensitivityAnalysis.objects.get(scenario=self.scenario, name='Conservative Scenario')
        assert analysis.return_adjustment == -0.02
        assert analysis.spending_adjustment == 0.10
        assert analysis.inflation_adjustment == 0.01
        # result_data field exists (may be empty or populated)
        assert analysis.result_data is not None
        assert analysis.description == 'Testing with conservative assumptions'

    def test_save_sensitivity_analysis_validation(self):
        """Test that saving requires valid data."""
        url = f'{self.api_url}/save/'
        data = {
            'name': '',  # Name is required
            'return_adjustment': 0.0,
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }

        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_saved_sensitivity_analyses(self):
        """Test listing saved sensitivity analyses for a scenario."""
        # Create some saved analyses
        SensitivityAnalysis.objects.create(
            scenario=self.scenario,
            name='Analysis 1',
            return_adjustment=-0.02,
            spending_adjustment=0.0,
            inflation_adjustment=0.0,
            result_data={}
        )
        SensitivityAnalysis.objects.create(
            scenario=self.scenario,
            name='Analysis 2',
            return_adjustment=0.0,
            spending_adjustment=0.20,
            inflation_adjustment=0.0,
            result_data={}
        )

        url = f'{self.api_url}/scenarios/'
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        analyses = response.json()
        assert len(analyses) == 2
        assert analyses[0]['name'] == 'Analysis 2'  # Most recent first
        assert analyses[1]['name'] == 'Analysis 1'

    def test_list_empty_sensitivity_analyses(self):
        """Test listing when no analyses exist."""
        url = f'{self.api_url}/scenarios/'
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        analyses = response.json()
        assert len(analyses) == 0

    def test_get_sensitivity_analysis_detail(self):
        """Test getting details of a specific sensitivity analysis."""
        # Create saved analysis
        analysis = SensitivityAnalysis.objects.create(
            scenario=self.scenario,
            name='Detail Test',
            description='Testing detail endpoint',
            return_adjustment=-0.03,
            spending_adjustment=0.15,
            inflation_adjustment=0.01,
            result_data={'success_rate': 90.0}
        )

        url = f'{self.api_url}/scenarios/{analysis.id}/'
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result['name'] == 'Detail Test'
        assert result['description'] == 'Testing detail endpoint'
        assert result['return_adjustment'] == -0.03
        assert result['spending_adjustment'] == 0.15
        assert result['inflation_adjustment'] == 0.01
        assert result['result_data']['success_rate'] == 90.0

    def test_get_nonexistent_sensitivity_analysis(self):
        """Test getting details of non-existent analysis returns 404."""
        url = f'{self.api_url}/scenarios/99999/'
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_access_other_users_scenario(self):
        """Test that users cannot access other users' scenarios."""
        # Create another user and scenario
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )

        FinancialProfile.objects.create(
            user=other_user,
            current_age=Decimal('60.00'),
            retirement_age=Decimal('65.00'),
            life_expectancy=95,
            current_portfolio_value=Decimal('1000000.00'),
            annual_spending=Decimal('40000.00')
        )

        other_scenario = RetirementScenario.objects.create(
            user=other_user,
            name='Other User Scenario',
            calculator_type='4_percent',
            parameters={}
        )

        # Update the auto-created result
        other_result = other_scenario.result
        other_result.status = 'completed'
        other_result.result_data = {'calculation': {}}
        other_result.save()

        # Try to access other user's scenario
        url = f'/api/v1/scenarios/{other_scenario.id}/sensitivity/calculate/'
        response = self.client.post(url, {
            'return_adjustment': 0.0,
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_endpoint_urls_are_correct(self):
        """Test that all sensitivity analysis endpoints have correct URL patterns."""
        # Calculate endpoint
        url = f'{self.api_url}/calculate/'
        response = self.client.post(url, {
            'return_adjustment': 0.0,
            'spending_adjustment': 0.0,
            'inflation_adjustment': 0.0
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

        # Tornado endpoint
        url = f'{self.api_url}/tornado/'
        response = self.client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_200_OK

        # List endpoint
        url = f'{self.api_url}/scenarios/'
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_expected_fields(self):
        """Test that API responses contain all expected fields."""
        # Test calculate response
        url = f'{self.api_url}/calculate/'
        response = self.client.post(url, {
            'return_adjustment': -0.01,
            'spending_adjustment': 0.05,
            'inflation_adjustment': 0.005
        }, format='json')

        result = response.json()
        expected_fields = [
            'success_rate', 'final_value', 'withdrawal_amount',
            'comparison_to_baseline', 'parameters_used', 'adjustments', 'execution_time_ms'
        ]
        for field in expected_fields:
            assert field in result, f"Expected field '{field}' not in response"

        # Test comparison_to_baseline fields
        comparison = result['comparison_to_baseline']
        comparison_fields = ['success_rate_delta', 'final_value_delta', 'final_value_percent_change']
        for field in comparison_fields:
            assert field in comparison, f"Expected field '{field}' not in comparison"
