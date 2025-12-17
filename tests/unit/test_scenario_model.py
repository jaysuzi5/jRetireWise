"""
Unit tests for RetirementScenario model updates (Phase 0 - Social Security Profile Enhancement).
"""

from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.scenarios.models import RetirementScenario


class RetirementScenarioSocialSecurityTestCase(TestCase):
    """Tests for RetirementScenario social security claiming age field."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_scenario_creation_with_default_claiming_age(self):
        """Test scenario defaults to claiming age 67."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='4_percent'
        )
        self.assertEqual(scenario.social_security_claiming_age, 67)

    def test_scenario_creation_with_age_62(self):
        """Test scenario can be created with claiming age 62."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Early Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=62
        )
        self.assertEqual(scenario.social_security_claiming_age, 62)

    def test_scenario_creation_with_age_65(self):
        """Test scenario can be created with claiming age 65."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Partial Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=65
        )
        self.assertEqual(scenario.social_security_claiming_age, 65)

    def test_scenario_creation_with_age_67(self):
        """Test scenario can be created with claiming age 67 (FRA)."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Full Retirement Age',
            calculator_type='4_percent',
            social_security_claiming_age=67
        )
        self.assertEqual(scenario.social_security_claiming_age, 67)

    def test_scenario_creation_with_age_70(self):
        """Test scenario can be created with claiming age 70."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Delayed Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=70
        )
        self.assertEqual(scenario.social_security_claiming_age, 70)

    def test_all_calculator_types_support_claiming_age(self):
        """Test all calculator types support claiming age field."""
        calculator_types = [
            '4_percent',
            '4_7_percent',
            'bucketed_withdrawal',
            'monte_carlo',
            'historical'
        ]
        for calc_type in calculator_types:
            scenario = RetirementScenario.objects.create(
                user=self.user,
                name=f'Scenario {calc_type}',
                calculator_type=calc_type,
                social_security_claiming_age=67
            )
            self.assertEqual(scenario.social_security_claiming_age, 67)

    def test_scenario_update_claiming_age(self):
        """Test scenario claiming age can be updated."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='4_percent',
            social_security_claiming_age=67
        )
        self.assertEqual(scenario.social_security_claiming_age, 67)

        # Update to age 62
        scenario.social_security_claiming_age = 62
        scenario.save()

        # Verify update
        refreshed = RetirementScenario.objects.get(id=scenario.id)
        self.assertEqual(refreshed.social_security_claiming_age, 62)

    def test_claiming_age_choices_display(self):
        """Test claiming age has proper choice display values."""
        expected_choices = [
            (62, '62 (Reduced benefit)'),
            (65, '65 (Partial benefit)'),
            (67, '67 (Full Retirement Age)'),
            (70, '70 (Delayed benefit)'),
        ]
        self.assertEqual(RetirementScenario.CLAIMING_AGE_CHOICES, expected_choices)

    def test_scenario_with_parameters_and_claiming_age(self):
        """Test scenario can have both parameters JSON and claiming age."""
        parameters = {
            'portfolio_value': 1000000,
            'withdrawal_rate': 0.04,
            'retirement_age': 65,
            'life_expectancy': 95
        }
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Full Scenario',
            calculator_type='4_percent',
            parameters=parameters,
            social_security_claiming_age=70
        )
        self.assertEqual(scenario.parameters, parameters)
        self.assertEqual(scenario.social_security_claiming_age, 70)

    def test_multiple_scenarios_different_claiming_ages(self):
        """Test user can have scenarios with different claiming ages."""
        scenario_62 = RetirementScenario.objects.create(
            user=self.user,
            name='Early',
            calculator_type='4_percent',
            social_security_claiming_age=62
        )
        scenario_70 = RetirementScenario.objects.create(
            user=self.user,
            name='Delayed',
            calculator_type='4_percent',
            social_security_claiming_age=70
        )

        self.assertEqual(scenario_62.social_security_claiming_age, 62)
        self.assertEqual(scenario_70.social_security_claiming_age, 70)
        self.assertNotEqual(scenario_62, scenario_70)

    def test_scenario_comparison_with_different_ages(self):
        """Test scenarios can be compared based on claiming age."""
        early = RetirementScenario.objects.create(
            user=self.user,
            name='Early Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=62
        )
        late = RetirementScenario.objects.create(
            user=self.user,
            name='Delayed Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=70
        )

        # Filter by claiming age
        late_claiming_scenarios = RetirementScenario.objects.filter(
            social_security_claiming_age=70
        )
        self.assertIn(late, late_claiming_scenarios)
        self.assertNotIn(early, late_claiming_scenarios)
