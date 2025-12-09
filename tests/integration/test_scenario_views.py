"""
Integration tests for scenario views and forms.
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from jretirewise.scenarios.models import RetirementScenario, WithdrawalBucket, CalculationResult


class ScenarioViewIntegrationTestCase(TestCase):
    """Test Scenario views with full request/response cycle."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_scenario_list_page_loads(self):
        """Test that scenario list page loads."""
        response = self.client.get('/dashboard/')
        assert response.status_code == 200

    def test_scenario_create_page_loads(self):
        """Test that scenario create page loads."""
        response = self.client.get('/dashboard/create/')
        assert response.status_code == 200
        assert 'Create' in response.content.decode() or 'Scenario' in response.content.decode()

    def test_scenario_create_requires_authentication(self):
        """Test that scenario creation requires login."""
        client = Client()
        response = client.get('/dashboard/create/')
        assert response.status_code == 302  # Redirect to login

    def test_create_simple_scenario(self):
        """Test creating a scenario with minimal data."""
        scenario_data = {
            'name': '4% Rule Plan',
            'description': 'Using the 4% rule strategy',
            'calculator_type': '4_percent',
            'parameters_json': '',
        }
        response = self.client.post('/dashboard/create/', scenario_data, follow=True)
        assert response.status_code == 200

        # Verify scenario was created
        scenario = RetirementScenario.objects.get(user=self.user, name='4% Rule Plan')
        assert scenario.calculator_type == '4_percent'
        assert scenario.user == self.user

    def test_create_scenario_with_parameters(self):
        """Test creating a scenario with JSON parameters."""
        params = {
            'annual_return': 0.07,
            'inflation_rate': 0.03,
            'withdrawal_rate': 0.04
        }
        scenario_data = {
            'name': 'Custom Parameters Plan',
            'description': 'Plan with custom parameters',
            'calculator_type': '4_7_percent',
            'parameters_json': json.dumps(params),
        }
        response = self.client.post('/dashboard/create/', scenario_data, follow=True)
        assert response.status_code == 200

        # Verify scenario and parameters were saved
        scenario = RetirementScenario.objects.get(user=self.user, name='Custom Parameters Plan')
        assert scenario.parameters == params

    def test_scenario_validation_error_display(self):
        """Test that validation errors are displayed."""
        invalid_data = {
            'name': 'Invalid Scenario',
            'description': 'Missing calculator type',
            'calculator_type': '',  # Required but empty
            'parameters_json': '',
        }
        response = self.client.post('/dashboard/create/', invalid_data)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'error' in content.lower() or 'required' in content.lower()

    def test_scenario_invalid_json_parameters(self):
        """Test that invalid JSON parameters are rejected."""
        scenario_data = {
            'name': 'Bad JSON Plan',
            'description': 'Plan with malformed JSON',
            'calculator_type': '4_percent',
            'parameters_json': '{invalid json}',  # Malformed JSON
        }
        response = self.client.post('/dashboard/create/', scenario_data)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Invalid JSON' in content or 'JSON' in content

    def test_scenario_list_shows_created_scenarios(self):
        """Test that created scenarios appear in list."""
        # Create multiple scenarios
        for i in range(3):
            RetirementScenario.objects.create(
                user=self.user,
                name=f'Scenario {i}',
                calculator_type='4_percent',
            )

        response = self.client.get('/dashboard/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Scenario 0' in content
        assert 'Scenario 1' in content
        assert 'Scenario 2' in content

    def test_scenario_detail_page_loads(self):
        """Test that scenario detail page loads."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='4_percent',
        )
        response = self.client.get(f'/dashboard/{scenario.id}/')
        assert response.status_code == 200
        assert 'Test Scenario' in response.content.decode()

    def test_user_can_only_see_own_scenarios(self):
        """Test that users can only see their own scenarios."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='TestPass123!'
        )

        # Create scenario for other user
        other_scenario = RetirementScenario.objects.create(
            user=other_user,
            name='Other User Scenario',
            calculator_type='4_percent',
        )

        # Try to access other user's scenario
        response = self.client.get(f'/dashboard/{other_scenario.id}/')
        assert response.status_code == 404

    def test_scenario_update(self):
        """Test updating a scenario."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description',
            calculator_type='4_percent',
        )

        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'calculator_type': '4_7_percent',
            'parameters_json': json.dumps({'annual_return': 0.06}),
        }
        response = self.client.post(f'/dashboard/{scenario.id}/edit/', update_data, follow=True)
        assert response.status_code == 200

        # Verify scenario was updated
        scenario.refresh_from_db()
        assert scenario.name == 'Updated Name'
        assert scenario.description == 'Updated description'
        assert scenario.calculator_type == '4_7_percent'
        assert scenario.parameters['annual_return'] == 0.06

    def test_scenario_all_calculator_types(self):
        """Test creating scenarios with all calculator types."""
        calculator_types = ['4_percent', '4_7_percent', 'monte_carlo', 'historical']

        for calc_type in calculator_types:
            scenario_data = {
                'name': f'Test {calc_type}',
                'description': f'Testing {calc_type}',
                'calculator_type': calc_type,
                'parameters_json': '',
            }
            response = self.client.post('/dashboard/create/', scenario_data, follow=True)
            assert response.status_code == 200

            # Verify scenario was created with correct type
            scenario = RetirementScenario.objects.get(user=self.user, name=f'Test {calc_type}')
            assert scenario.calculator_type == calc_type

    def test_scenario_required_fields(self):
        """Test that required fields are enforced."""
        # Missing name
        data = {
            'description': 'Missing name',
            'calculator_type': '4_percent',
            'parameters_json': '',
        }
        response = self.client.post('/dashboard/create/', data)
        assert response.status_code == 200
        content = response.content.decode().lower()
        assert 'required' in content or 'error' in content

    def test_scenario_success_message(self):
        """Test that success message is displayed after creation."""
        scenario_data = {
            'name': 'Test Scenario',
            'description': 'Testing success message',
            'calculator_type': '4_percent',
            'parameters_json': '',
        }
        response = self.client.post('/dashboard/create/', scenario_data, follow=True)
        assert response.status_code == 200
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert 'created successfully' in str(messages[0]).lower()


class WithdrawalBucketAPITestCase(APITestCase):
    """Test WithdrawalBucket API endpoints."""

    def setUp(self):
        """Set up test user and API client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='TestPass123!'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create a scenario for testing
        self.scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'portfolio_value': 1000000,
                'retirement_age': 65,
                'life_expectancy': 95,
                'annual_return_rate': 0.07,
                'inflation_rate': 0.03,
            }
        )

    def test_create_withdrawal_bucket(self):
        """Test creating a withdrawal bucket via API."""
        bucket_data = {
            'scenario': self.scenario.id,
            'bucket_name': 'Early Retirement (65-70)',
            'description': 'High withdrawal rate before Social Security',
            'start_age': 65,
            'end_age': 70,
            'target_withdrawal_rate': 4.5,
            'expected_pension_income': 0,
            'expected_social_security_income': 0,
            'order': 1,
        }
        response = self.client.post('/api/v1/withdrawal-buckets/', bucket_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['bucket_name'] == 'Early Retirement (65-70)'
        assert WithdrawalBucket.objects.count() == 1

    def test_list_withdrawal_buckets(self):
        """Test listing withdrawal buckets."""
        # Create multiple buckets
        for i in range(3):
            WithdrawalBucket.objects.create(
                scenario=self.scenario,
                bucket_name=f'Bucket {i}',
                start_age=65 + i * 5,
                target_withdrawal_rate=4.0 - i * 0.5,
                order=i,
            )

        response = self.client.get('/api/v1/withdrawal-buckets/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_retrieve_withdrawal_bucket(self):
        """Test retrieving a single bucket."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Test Bucket',
            start_age=65,
            target_withdrawal_rate=4.0,
            order=1,
        )
        response = self.client.get(f'/api/v1/withdrawal-buckets/{bucket.id}/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['bucket_name'] == 'Test Bucket'

    def test_update_withdrawal_bucket(self):
        """Test updating a bucket."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Original Name',
            start_age=65,
            target_withdrawal_rate=4.0,
            order=1,
        )
        update_data = {
            'bucket_name': 'Updated Name',
            'target_withdrawal_rate': 3.5,
        }
        response = self.client.patch(f'/api/v1/withdrawal-buckets/{bucket.id}/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        bucket.refresh_from_db()
        assert bucket.bucket_name == 'Updated Name'
        assert bucket.target_withdrawal_rate == 3.5

    def test_delete_withdrawal_bucket(self):
        """Test deleting a bucket."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='To Delete',
            start_age=65,
            target_withdrawal_rate=4.0,
            order=1,
        )
        response = self.client.delete(f'/api/v1/withdrawal-buckets/{bucket.id}/', format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert WithdrawalBucket.objects.filter(id=bucket.id).count() == 0

    def test_user_can_only_see_own_buckets(self):
        """Test that users can only see their own buckets."""
        other_scenario = RetirementScenario.objects.create(
            user=self.other_user,
            name='Other User Scenario',
            calculator_type='bucketed_withdrawal',
        )
        other_bucket = WithdrawalBucket.objects.create(
            scenario=other_scenario,
            bucket_name='Other User Bucket',
            start_age=65,
            target_withdrawal_rate=4.0,
            order=1,
        )
        response = self.client.get('/api/v1/withdrawal-buckets/', format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_validate_bucket_overlap(self):
        """Test bucket overlap validation."""
        buckets_data = [
            {
                'bucket_name': 'Bucket 1',
                'start_age': 65,
                'end_age': 70,
            },
            {
                'bucket_name': 'Bucket 2',
                'start_age': 68,  # Overlaps with Bucket 1
                'end_age': 75,
            }
        ]
        response = self.client.post(
            '/api/v1/withdrawal-buckets/validate-overlap/',
            {'buckets': buckets_data},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert not response.data['valid']
        assert len(response.data['errors']) > 0

    def test_validate_bucket_no_overlap(self):
        """Test validation passes for non-overlapping buckets."""
        buckets_data = [
            {
                'bucket_name': 'Bucket 1',
                'start_age': 65,
                'end_age': 70,
            },
            {
                'bucket_name': 'Bucket 2',
                'start_age': 71,
                'end_age': 80,
            }
        ]
        response = self.client.post(
            '/api/v1/withdrawal-buckets/validate-overlap/',
            {'buckets': buckets_data},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid']


class BucketedWithdrawalCalculationAPITestCase(APITestCase):
    """Test bucketed withdrawal calculation API endpoint."""

    def setUp(self):
        """Set up test user and scenario."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create a scenario with parameters
        self.scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Bucketed Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'portfolio_value': 1000000,
                'retirement_age': 65,
                'life_expectancy': 95,
                'annual_return_rate': 0.07,
                'inflation_rate': 0.03,
            }
        )

        # Create withdrawal buckets
        WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Age 65-70',
            start_age=65,
            end_age=70,
            target_withdrawal_rate=4.5,
            order=1,
        )
        WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Age 70-80',
            start_age=70,
            end_age=80,
            target_withdrawal_rate=3.5,
            expected_social_security_income=30000,
            order=2,
        )
        WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Age 80+',
            start_age=80,
            target_withdrawal_rate=2.5,
            expected_social_security_income=30000,
            order=3,
        )

    def test_calculate_bucketed_withdrawal(self):
        """Test running a bucketed withdrawal calculation."""
        response = self.client.post(
            f'/api/v1/scenarios/{self.scenario.id}/calculate/bucketed-withdrawal/',
            {},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'result_data' in response.data
        assert 'projections' in response.data['result_data']
        assert 'summary' in response.data['result_data']
        assert len(response.data['result_data']['projections']) > 0

    def test_calculation_missing_buckets(self):
        """Test calculation fails when scenario has no buckets."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='No Buckets Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'portfolio_value': 1000000,
                'retirement_age': 65,
                'life_expectancy': 95,
            }
        )
        response = self.client.post(
            f'/api/v1/scenarios/{scenario.id}/calculate/bucketed-withdrawal/',
            {},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'no withdrawal buckets' in response.data['error'].lower()

    def test_calculation_missing_parameters(self):
        """Test calculation fails when scenario has missing parameters."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Missing Params Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={'portfolio_value': 1000000}  # Missing other required params
        )
        response = self.client.post(
            f'/api/v1/scenarios/{scenario.id}/calculate/bucketed-withdrawal/',
            {},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'missing required parameters' in response.data['error'].lower()

    def test_calculation_result_stored(self):
        """Test that calculation results are stored in database."""
        response = self.client.post(
            f'/api/v1/scenarios/{self.scenario.id}/calculate/bucketed-withdrawal/',
            {},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify result was stored
        calculation_result = CalculationResult.objects.get(scenario=self.scenario)
        assert calculation_result.status == 'completed'
        assert calculation_result.execution_time_ms >= 0  # Could be 0 on very fast systems
        assert 'projections' in calculation_result.result_data

    def test_calculation_projects_30_years(self):
        """Test that calculation projects the correct time span."""
        response = self.client.post(
            f'/api/v1/scenarios/{self.scenario.id}/calculate/bucketed-withdrawal/',
            {},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        projections = response.data['result_data']['projections']
        # 95 - 65 = 30 years
        assert len(projections) == 31  # Including year 0
