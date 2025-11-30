"""
Integration tests for scenario views and forms.
"""

import pytest
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from jretirewise.scenarios.models import RetirementScenario


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
