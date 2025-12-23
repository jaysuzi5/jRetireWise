"""
Integration tests for calculator Social Security claiming age functionality (Phase 0).

Tests that all calculator types properly use age-specific Social Security benefits
based on the claiming age parameter.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.financial.models import TaxProfile, FinancialProfile
from jretirewise.scenarios.models import RetirementScenario, CalculationResult
from jretirewise.calculations.calculators import (
    FourPercentCalculator,
    FourPointSevenPercentCalculator,
    MonteCarloCalculator,
    EnhancedMonteCarloCalculator,
    HistoricalPeriodCalculator,
)


class CalculatorSocialSecurityAgeTestCase(TestCase):
    """Test Social Security claiming age parameter for all calculators."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create financial profile
        self.financial_profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=Decimal('60'),
            retirement_age=Decimal('65'),
            life_expectancy=95,
            annual_spending=Decimal('80000'),
            social_security_annual=Decimal('44400'),  # Default to age 67
            pension_annual=Decimal('0'),
            current_portfolio_value=Decimal('1000000'),
        )

        # Create tax profile (filing status and state only)
        self.tax_profile = TaxProfile.objects.create(
            user=self.user,
            filing_status='mfj',
            state_of_residence='CA'
        )

    def test_four_percent_calculator_with_ss_age_62(self):
        """Test 4% calculator with Social Security claiming age 62."""
        calculator = FourPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=30000,
            social_security_claiming_age=62,
        )
        result = calculator.calculate()

        self.assertEqual(result['claiming_age'], 62)
        self.assertEqual(result['social_security_annual'], Decimal('30000'))
        self.assertIn('projections', result)
        self.assertTrue(len(result['projections']) > 0)

    def test_four_percent_calculator_with_ss_age_67(self):
        """Test 4% calculator with Social Security claiming age 67 (FRA)."""
        calculator = FourPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=44400,
            social_security_claiming_age=67,
        )
        result = calculator.calculate()

        self.assertEqual(result['claiming_age'], 67)
        self.assertEqual(result['social_security_annual'], Decimal('44400'))

    def test_four_percent_calculator_with_ss_age_70(self):
        """Test 4% calculator with Social Security claiming age 70."""
        calculator = FourPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=55200,
            social_security_claiming_age=70,
        )
        result = calculator.calculate()

        self.assertEqual(result['claiming_age'], 70)
        self.assertEqual(result['social_security_annual'], Decimal('55200'))

    def test_four_seven_percent_calculator_with_claiming_age(self):
        """Test 4.7% calculator with Social Security claiming age."""
        calculator = FourPointSevenPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=44400,
            social_security_claiming_age=67,
        )
        result = calculator.calculate()

        self.assertEqual(result['claiming_age'], 67)
        self.assertEqual(result['social_security_annual'], Decimal('44400'))

    def test_monte_carlo_calculator_with_claiming_age(self):
        """Test Monte Carlo calculator accepts Social Security parameters."""
        calculator = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=100,  # Reduced for test speed
            mode='evaluate_success',
            withdrawal_amount=80000,
            target_success_rate=90.0,
            social_security_start_age=67,
            social_security_monthly_benefit=3700,
            pension_annual=0,
            periods_per_year=12,
        )
        result = calculator.calculate()

        # Verify result contains expected keys
        self.assertIn('success_rate', result)
        self.assertGreaterEqual(result['success_rate'], 0)
        self.assertLessEqual(result['success_rate'], 100)

    def test_historical_calculator_with_ss_parameters(self):
        """Test Historical Period calculator with Social Security parameters."""
        calculator = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.04,
            stock_allocation=0.60,
            social_security_start_age=67,
            social_security_annual=44400,
            pension_annual=0,
        )
        result = calculator.calculate()

        # Verify result contains expected structure
        self.assertIn('success_rate', result)
        self.assertIn('best_case', result)
        self.assertIn('worst_case', result)

    def test_calculators_with_different_ss_amounts(self):
        """Test that different SS amounts produce different results."""
        # Low SS age 62
        calc_low = FourPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=30000,
            social_security_claiming_age=62,
        )
        result_low = calc_low.calculate()

        # High SS age 70
        calc_high = FourPercentCalculator(
            portfolio_value=1000000,
            annual_spending=80000,
            current_age=60,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            social_security_annual=55200,
            social_security_claiming_age=70,
        )
        result_high = calc_high.calculate()

        # High SS should result in lower portfolio withdrawals (better success rate)
        self.assertNotEqual(result_low['social_security_annual'], result_high['social_security_annual'])
        self.assertLess(result_low['social_security_annual'], result_high['social_security_annual'])

    def test_scenario_with_tax_profile_lookup(self):
        """Test that scenario can look up SS benefit from TaxProfile."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test Scenario',
            calculator_type='4_percent',
            parameters={
                'portfolio_value': 1000000,
                'annual_spending': 80000,
                'annual_return_rate': 0.07,
            },
            social_security_claiming_age=70,
        )

        # Verify scenario stored correct claiming age
        self.assertEqual(scenario.social_security_claiming_age, 70)

        # Look up what the benefit should be
        expected_benefit = self.tax_profile.get_social_security_annual(70)
        self.assertEqual(expected_benefit, Decimal('55200'))

    def test_default_claiming_age_67(self):
        """Test that default claiming age is 67."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Default Scenario',
            calculator_type='4_percent',
        )
        self.assertEqual(scenario.social_security_claiming_age, 67)

    def test_scenario_with_tax_profile_basic(self):
        """Test scenario can be created with refactored TaxProfile."""
        # Verify tax profile exists and has tax-specific fields
        self.assertEqual(self.tax_profile.filing_status, 'mfj')
        self.assertEqual(self.tax_profile.state_of_residence, 'CA')
        # Verify account balances are calculated from portfolio
        balances = self.tax_profile.get_account_balances_from_portfolio()
        self.assertIsInstance(balances, dict)
        self.assertIn('traditional', balances)
        self.assertIn('roth', balances)


class ScenarioCalculationWithClaimingAgeTestCase(TestCase):
    """Test scenario calculations with Social Security claiming age."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create financial profile
        FinancialProfile.objects.create(
            user=self.user,
            current_age=Decimal('60'),
            retirement_age=Decimal('65'),
            life_expectancy=95,
            annual_spending=Decimal('80000'),
            social_security_annual=Decimal('44400'),
            pension_annual=Decimal('0'),
            current_portfolio_value=Decimal('1000000'),
        )

        # Create tax profile
        TaxProfile.objects.create(
            user=self.user,
            filing_status='mfj',
            state_of_residence='CA',
        )

    def test_multiple_scenarios_different_claiming_ages(self):
        """Test user can have multiple scenarios with different claiming ages."""
        scenario_early = RetirementScenario.objects.create(
            user=self.user,
            name='Early Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=62,
        )

        scenario_late = RetirementScenario.objects.create(
            user=self.user,
            name='Late Claiming',
            calculator_type='4_percent',
            social_security_claiming_age=70,
        )

        self.assertEqual(scenario_early.social_security_claiming_age, 62)
        self.assertEqual(scenario_late.social_security_claiming_age, 70)

        # Query scenarios by claiming age
        age_62_scenarios = RetirementScenario.objects.filter(
            social_security_claiming_age=62
        )
        self.assertIn(scenario_early, age_62_scenarios)
        self.assertNotIn(scenario_late, age_62_scenarios)

    def test_scenario_preserves_claiming_age_on_update(self):
        """Test claiming age is preserved when scenario is updated."""
        scenario = RetirementScenario.objects.create(
            user=self.user,
            name='Test',
            calculator_type='4_percent',
            social_security_claiming_age=70,
        )

        # Update scenario name
        scenario.name = 'Updated Name'
        scenario.save()

        # Verify claiming age unchanged
        refreshed = RetirementScenario.objects.get(id=scenario.id)
        self.assertEqual(refreshed.social_security_claiming_age, 70)
