"""
Integration tests for bucketed withdrawal scenario and bucket views.
"""

import pytest
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from jretirewise.financial.models import FinancialProfile
from jretirewise.scenarios.models import RetirementScenario, WithdrawalBucket, CalculationResult


class BucketedWithdrawalScenarioViewIntegrationTestCase(TestCase):
    """Test Bucketed Withdrawal Scenario views with full request/response cycle."""

    def setUp(self):
        """Set up test user with financial profile."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=45,
            retirement_age=65,
            life_expectancy=90,
            annual_spending=Decimal('80000.00'),
            social_security_annual=Decimal('20000.00'),
            pension_annual=Decimal('0.00'),
            current_portfolio_value=Decimal('1000000.00'),
        )

        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_bucketed_scenario_create_page_loads(self):
        """Test that bucketed withdrawal scenario create page loads."""
        response = self.client.get(reverse('scenario-bucketed-create'))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Bucketed Withdrawal' in content or 'Bucket' in content

    def test_bucketed_scenario_create_requires_authentication(self):
        """Test that scenario creation requires login."""
        client = Client()
        response = client.get(reverse('scenario-bucketed-create'))
        assert response.status_code == 302  # Redirect to login

    def test_create_bucketed_scenario_minimal(self):
        """Test creating a bucketed withdrawal scenario with minimal data."""
        scenario_data = {
            'name': 'Bucketed Plan',
            'description': 'A bucketed withdrawal strategy',
            'retirement_age': '65',
            'life_expectancy': '90',
            'portfolio_value': '1000000.00',
            'expected_return': '7.0',
            'inflation_rate': '3.0',
        }
        response = self.client.post(reverse('scenario-bucketed-create'), scenario_data, follow=True)
        assert response.status_code == 200

        # Verify scenario was created
        scenario = RetirementScenario.objects.get(user=self.user, name='Bucketed Plan')
        assert scenario.calculator_type == 'bucketed_withdrawal'
        assert scenario.user == self.user
        assert scenario.parameters['annual_return_rate'] == Decimal('0.07')
        assert scenario.parameters['inflation_rate'] == Decimal('0.03')

    def test_create_bucketed_scenario_with_description(self):
        """Test creating scenario with detailed description."""
        scenario_data = {
            'name': 'Detailed Bucketed Plan',
            'description': 'A comprehensive bucketed withdrawal plan with multiple age buckets',
            'retirement_age': '62',
            'life_expectancy': '95',
            'portfolio_value': '1500000.00',
            'expected_return': '6.5',
            'inflation_rate': '2.5',
        }
        response = self.client.post(reverse('scenario-bucketed-create'), scenario_data, follow=True)
        assert response.status_code == 200

        scenario = RetirementScenario.objects.get(user=self.user, name='Detailed Bucketed Plan')
        assert scenario.description == 'A comprehensive bucketed withdrawal plan with multiple age buckets'

    def test_create_bucketed_scenario_form_prepopulated(self):
        """Test that form is pre-populated from user profile."""
        response = self.client.get(reverse('scenario-bucketed-create'))
        assert response.status_code == 200
        content = response.content.decode()
        # Should show indicators that fields are pre-filled
        assert 'from portfolio' in content.lower() or 'prefilled' in content.lower() or '1000000' in content

    def test_create_bucketed_scenario_invalid_ages(self):
        """Test that invalid age relationships are rejected."""
        scenario_data = {
            'name': 'Invalid Ages',
            'description': 'Invalid age scenario',
            'retirement_age': '90',
            'life_expectancy': '65',  # Invalid
            'portfolio_value': '1000000.00',
            'expected_return': '7.0',
            'inflation_rate': '3.0',
        }
        response = self.client.post(reverse('scenario-bucketed-create'), scenario_data)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'error' in content.lower() or 'required' in content.lower()

    def test_bucketed_scenario_edit_page_loads(self):
        """Test that bucketed scenario edit page loads."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'retirement_age': 65,
                'life_expectancy': 90,
                'portfolio_value': Decimal('1000000.00'),
                'annual_return_rate': Decimal('0.07'),
                'inflation_rate': Decimal('0.03'),
            }
        )
        response = self.client.get(reverse('scenario-bucketed-edit', args=[scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Edit' in content or 'Bucketed' in content

    def test_edit_bucketed_scenario(self):
        """Test editing a bucketed withdrawal scenario."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Original Name',
            calculator_type='bucketed_withdrawal',
            parameters={
                'retirement_age': 65,
                'life_expectancy': 90,
                'portfolio_value': Decimal('1000000.00'),
                'annual_return_rate': Decimal('0.07'),
                'inflation_rate': Decimal('0.03'),
            }
        )

        scenario_data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'retirement_age': '63',
            'life_expectancy': '92',
            'portfolio_value': '1200000.00',
            'expected_return': '6.5',
            'inflation_rate': '2.5',
        }
        response = self.client.post(
            reverse('scenario-bucketed-edit', args=[scenario.id]),
            scenario_data,
            follow=True
        )
        assert response.status_code == 200

        # Verify scenario was updated
        scenario.refresh_from_db()
        assert scenario.name == 'Updated Name'
        assert scenario.parameters['portfolio_value'] == Decimal('1200000.00')

    def test_cannot_edit_other_users_scenario(self):
        """Test that users cannot edit other users' scenarios."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        scenario = RetirementScenario.objects.create(
            user=other_user,
            name='Other User Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'retirement_age': 65,
                'life_expectancy': 90,
                'portfolio_value': Decimal('1000000.00'),
                'annual_return_rate': Decimal('0.07'),
                'inflation_rate': Decimal('0.03'),
            }
        )

        response = self.client.get(reverse('scenario-bucketed-edit', args=[scenario.id]))
        # Should get 404 or redirect
        assert response.status_code in [404, 302]


class WithdrawalBucketViewIntegrationTestCase(TestCase):
    """Test Withdrawal Bucket CRUD views with full request/response cycle."""

    def setUp(self):
        """Set up test user and scenario."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={
                'retirement_age': 65,
                'life_expectancy': 90,
                'portfolio_value': Decimal('1000000.00'),
                'annual_return_rate': Decimal('0.07'),
                'inflation_rate': Decimal('0.03'),
            }
        )

        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_bucket_list_page_loads(self):
        """Test that bucket list page loads."""
        response = self.client.get(reverse('bucket-list', args=[self.scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Withdrawal Bucket' in content or 'Bucket' in content

    def test_bucket_list_requires_authentication(self):
        """Test that bucket list requires login."""
        client = Client()
        response = client.get(reverse('bucket-list', args=[self.scenario.id]))
        assert response.status_code == 302  # Redirect to login

    def test_bucket_list_shows_scenario_info(self):
        """Test that bucket list displays scenario information."""
        response = self.client.get(reverse('bucket-list', args=[self.scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert self.scenario.name in content
        assert 'Retirement Age' in content

    def test_bucket_create_page_loads(self):
        """Test that bucket create page loads."""
        response = self.client.get(reverse('bucket-create', args=[self.scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Create' in content or 'Bucket' in content

    def test_create_bucket(self):
        """Test creating a withdrawal bucket."""
        bucket_data = {
            'bucket_name': 'Early Retirement (65-72)',
            'order': 1,
            'description': 'High withdrawal period',
            'start_age': '65',
            'end_age': '72',
            'target_withdrawal_rate': '4.5',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '30000.00',
            'max_withdrawal_amount': '100000.00',
            'expected_pension_income': '0.00',
            'expected_social_security_income': '0.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }
        response = self.client.post(
            reverse('bucket-create', args=[self.scenario.id]),
            bucket_data,
            follow=True
        )
        assert response.status_code == 200

        # Verify bucket was created
        bucket = WithdrawalBucket.objects.get(
            scenario=self.scenario,
            bucket_name='Early Retirement (65-72)'
        )
        assert bucket.start_age == 65
        assert bucket.end_age == 72
        assert bucket.target_withdrawal_rate == Decimal('4.5')

    def test_create_multiple_buckets(self):
        """Test creating multiple buckets for same scenario."""
        bucket1_data = {
            'bucket_name': 'Early (65-72)',
            'order': 1,
            'description': '',
            'start_age': '65',
            'end_age': '72',
            'target_withdrawal_rate': '4.5',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '30000.00',
            'max_withdrawal_amount': '100000.00',
            'expected_pension_income': '0.00',
            'expected_social_security_income': '0.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }

        bucket2_data = {
            'bucket_name': 'Middle (73-82)',
            'order': 2,
            'description': '',
            'start_age': '73',
            'end_age': '82',
            'target_withdrawal_rate': '3.5',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '20000.00',
            'max_withdrawal_amount': '80000.00',
            'expected_pension_income': '0.00',
            'expected_social_security_income': '0.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }

        # Create first bucket
        response1 = self.client.post(
            reverse('bucket-create', args=[self.scenario.id]),
            bucket1_data,
            follow=True
        )
        assert response1.status_code == 200

        # Create second bucket
        response2 = self.client.post(
            reverse('bucket-create', args=[self.scenario.id]),
            bucket2_data,
            follow=True
        )
        assert response2.status_code == 200

        # Verify both buckets exist
        buckets = WithdrawalBucket.objects.filter(scenario=self.scenario).order_by('order')
        assert buckets.count() == 2
        assert buckets[0].bucket_name == 'Early (65-72)'
        assert buckets[1].bucket_name == 'Middle (73-82)'

    def test_bucket_edit_page_loads(self):
        """Test that bucket edit page loads."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Test Bucket',
            start_age=65,
            end_age=75,
            target_withdrawal_rate=Decimal('4.5'),
        )
        response = self.client.get(reverse('bucket-edit', args=[bucket.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Test Bucket' in content or 'Edit' in content

    def test_edit_bucket(self):
        """Test editing a withdrawal bucket."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Original Name',
            start_age=65,
            end_age=75,
            target_withdrawal_rate=Decimal('4.5'),
        )

        bucket_data = {
            'bucket_name': 'Updated Name',
            'order': 1,
            'description': 'Updated description',
            'start_age': '66',
            'end_age': '76',
            'target_withdrawal_rate': '4.0',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '30000.00',
            'max_withdrawal_amount': '100000.00',
            'expected_pension_income': '0.00',
            'expected_social_security_income': '0.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }

        response = self.client.post(
            reverse('bucket-edit', args=[bucket.id]),
            bucket_data,
            follow=True
        )
        assert response.status_code == 200

        # Verify bucket was updated
        bucket.refresh_from_db()
        assert bucket.bucket_name == 'Updated Name'
        assert bucket.start_age == 66
        assert bucket.end_age == 76

    def test_bucket_delete_page_loads(self):
        """Test that bucket delete page loads."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Delete Test',
            start_age=65,
            end_age=75,
            target_withdrawal_rate=Decimal('4.5'),
        )
        response = self.client.get(reverse('bucket-delete', args=[bucket.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Delete Test' in content or 'delete' in content.lower()

    def test_delete_bucket(self):
        """Test deleting a withdrawal bucket."""
        bucket = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Delete Me',
            start_age=65,
            end_age=75,
            target_withdrawal_rate=Decimal('4.5'),
        )
        bucket_id = bucket.id

        response = self.client.post(
            reverse('bucket-delete', args=[bucket.id]),
            follow=True
        )
        assert response.status_code == 200

        # Verify bucket was deleted
        assert not WithdrawalBucket.objects.filter(id=bucket_id).exists()

    def test_bucket_list_displays_buckets(self):
        """Test that bucket list displays all buckets for scenario."""
        bucket1 = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Bucket 1',
            order=1,
            start_age=65,
            end_age=72,
            target_withdrawal_rate=Decimal('4.5'),
        )
        bucket2 = WithdrawalBucket.objects.create(
            scenario=self.scenario,
            bucket_name='Bucket 2',
            order=2,
            start_age=73,
            end_age=82,
            target_withdrawal_rate=Decimal('3.5'),
        )

        response = self.client.get(reverse('bucket-list', args=[self.scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Bucket 1' in content
        assert 'Bucket 2' in content
        assert '65-72' in content or '65' in content
        assert '73-82' in content or '73' in content

    def test_bucket_list_empty_state(self):
        """Test bucket list empty state when no buckets exist."""
        response = self.client.get(reverse('bucket-list', args=[self.scenario.id]))
        assert response.status_code == 200
        content = response.content.decode()
        # Should show empty state message
        assert 'No' in content or 'empty' in content.lower() or 'Add' in content

    def test_cannot_access_other_users_buckets(self):
        """Test that users cannot access other users' buckets."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        other_scenario = RetirementScenario.objects.create(
            user=other_user,
            name='Other Scenario',
            calculator_type='bucketed_withdrawal',
            parameters={}
        )
        bucket = WithdrawalBucket.objects.create(
            scenario=other_scenario,
            bucket_name='Other User Bucket',
            start_age=65,
            end_age=75,
            target_withdrawal_rate=Decimal('4.5'),
        )

        response = self.client.get(reverse('bucket-edit', args=[bucket.id]))
        # Should get 404 or redirect
        assert response.status_code in [404, 302]

    def test_bucket_create_invalid_form(self):
        """Test that invalid bucket form is rejected."""
        bucket_data = {
            'bucket_name': 'Invalid Bucket',
            'order': 1,
            'description': '',
            'start_age': '80',
            'end_age': '65',  # Invalid: end_age < start_age
            'target_withdrawal_rate': '4.5',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '30000.00',
            'max_withdrawal_amount': '100000.00',
            'expected_pension_income': '0.00',
            'expected_social_security_income': '0.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }
        response = self.client.post(
            reverse('bucket-create', args=[self.scenario.id]),
            bucket_data
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'error' in content.lower() or 'required' in content.lower()

    def test_bucket_with_income_sources(self):
        """Test creating bucket with pension and social security income."""
        bucket_data = {
            'bucket_name': 'With Income',
            'order': 1,
            'description': '',
            'start_age': '70',
            'end_age': '85',
            'target_withdrawal_rate': '3.0',
            'manual_withdrawal_override': '',
            'min_withdrawal_amount': '10000.00',
            'max_withdrawal_amount': '50000.00',
            'expected_pension_income': '20000.00',
            'expected_social_security_income': '25000.00',
            'healthcare_cost_adjustment': '0.00',
            'tax_loss_harvesting_enabled': False,
            'roth_conversion_enabled': False,
        }
        response = self.client.post(
            reverse('bucket-create', args=[self.scenario.id]),
            bucket_data,
            follow=True
        )
        assert response.status_code == 200

        bucket = WithdrawalBucket.objects.get(
            scenario=self.scenario,
            bucket_name='With Income'
        )
        assert bucket.expected_pension_income == Decimal('20000.00')
        assert bucket.expected_social_security_income == Decimal('25000.00')
