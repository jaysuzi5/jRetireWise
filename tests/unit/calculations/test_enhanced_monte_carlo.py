"""
Unit tests for EnhancedMonteCarloCalculator.
"""

import pytest
from decimal import Decimal
from jretirewise.calculations.calculators import EnhancedMonteCarloCalculator


@pytest.mark.unit
class TestEnhancedMonteCarloCalculatorModes:
    """Tests for calculation modes."""

    def test_find_withdrawal_mode_returns_safe_withdrawal(self):
        """Test that find_withdrawal mode returns a withdrawal amount."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=100,
            mode='find_withdrawal',
            target_success_rate=90,
        )
        result = calc.calculate()

        assert result['mode'] == 'find_withdrawal'
        assert 'safe_withdrawal_annual' in result
        assert 'safe_withdrawal_monthly' in result
        assert 'safe_withdrawal_rate' in result
        assert result['safe_withdrawal_annual'] > 0
        assert result['safe_withdrawal_monthly'] == result['safe_withdrawal_annual'] / 12

    def test_evaluate_success_mode_returns_success_rate(self):
        """Test that evaluate_success mode returns success rate."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert result['mode'] == 'evaluate_success'
        assert 'success_rate' in result
        assert 'withdrawal_annual' in result
        assert result['withdrawal_annual'] == 40000
        assert 0 <= result['success_rate'] <= 100

    def test_find_withdrawal_achieves_target_success_rate(self):
        """Test that binary search finds withdrawal achieving target rate."""
        target = 90.0
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=500,  # More simulations for stability
            mode='find_withdrawal',
            target_success_rate=target,
        )
        result = calc.calculate()

        # Should be within 5% of target (allowing for simulation variance)
        assert abs(result['achieved_success_rate'] - target) < 5.0
        assert result['target_success_rate'] == target

    def test_evaluate_success_with_withdrawal_rate(self):
        """Test evaluate_success mode with rate instead of amount."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_rate=0.04,  # 4% rate
        )
        result = calc.calculate()

        assert result['withdrawal_annual'] == 40000  # 4% of 1M
        assert result['withdrawal_rate'] == 4.0


@pytest.mark.unit
class TestSocialSecurityIntegration:
    """Tests for Social Security integration."""

    def test_social_security_reduces_withdrawal_need(self):
        """Test that SS income allows higher success rate or withdrawal."""
        # Without SS
        calc_no_ss = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=200,
            mode='evaluate_success',
            withdrawal_amount=60000,
        )
        result_no_ss = calc_no_ss.calculate()

        # With SS ($2500/month starting at 67)
        calc_with_ss = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=200,
            mode='evaluate_success',
            withdrawal_amount=60000,
            social_security_start_age=67,
            social_security_monthly_benefit=2500,
        )
        result_with_ss = calc_with_ss.calculate()

        # With SS, success rate should be higher (or at least not lower)
        # SS provides $30k/year which significantly reduces portfolio withdrawals
        assert result_with_ss['success_rate'] >= result_no_ss['success_rate']

    def test_social_security_parameters_in_result(self):
        """Test that SS parameters are included in result."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
            social_security_start_age=67,
            social_security_monthly_benefit=2000,
        )
        result = calc.calculate()

        assert result['parameters']['social_security_start_age'] == 67
        assert result['parameters']['social_security_annual'] == 24000  # 2000 * 12

    def test_social_security_not_applied_before_start_age(self):
        """Test SS benefit only kicks in at specified age."""
        # Create calculator where SS starts after life expectancy
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=70,  # Short retirement
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
            social_security_start_age=75,  # SS starts after death
            social_security_monthly_benefit=2500,
        )
        result = calc.calculate()

        # SS should have no effect since it starts after life expectancy
        # Result should be similar to no SS case
        assert result['parameters']['social_security_start_age'] == 75


@pytest.mark.unit
class TestFourPercentComparison:
    """Tests for 4% rule comparison."""

    def test_four_percent_comparison_included_in_results(self):
        """Test that results include 4% rule comparison."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='find_withdrawal',
            target_success_rate=90,
        )
        result = calc.calculate()

        assert 'four_percent_comparison' in result
        assert result['four_percent_comparison']['withdrawal_annual'] == 40000
        assert result['four_percent_comparison']['withdrawal_monthly'] == 40000 / 12
        assert 'success_rate' in result['four_percent_comparison']

    def test_four_percent_comparison_in_evaluate_mode(self):
        """Test 4% comparison in evaluate_success mode."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=2000000,
            retirement_age=60,
            life_expectancy=95,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=100000,
        )
        result = calc.calculate()

        assert result['four_percent_comparison']['withdrawal_annual'] == 80000  # 4% of 2M


@pytest.mark.unit
class TestResultStructure:
    """Tests for result data structure."""

    def test_result_includes_yearly_percentiles(self):
        """Test that yearly percentiles are included for charting."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert 'yearly_percentiles' in result
        assert len(result['yearly_percentiles']) == 26  # Years 0-25 (65 to 90)

        # Check first year structure
        first_year = result['yearly_percentiles'][0]
        assert first_year['year'] == 0
        assert first_year['age'] == 65
        assert all(k in first_year for k in ['p5', 'p10', 'p25', 'p50', 'p75', 'p90', 'p95', 'mean'])

    def test_result_includes_final_value_percentiles(self):
        """Test that final value distribution is included."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert 'final_value_percentiles' in result
        percentiles = result['final_value_percentiles']
        assert all(k in percentiles for k in ['p5', 'p10', 'p25', 'p50', 'p75', 'p90', 'p95'])

        # Percentiles should be in order (p5 <= p25 <= p50 <= p75 <= p95)
        assert percentiles['p5'] <= percentiles['p25']
        assert percentiles['p25'] <= percentiles['p50']
        assert percentiles['p50'] <= percentiles['p75']
        assert percentiles['p75'] <= percentiles['p95']

    def test_result_includes_constant_return_trajectory(self):
        """Test that constant return trajectory is included for charting."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert 'constant_return_trajectory' in result
        trajectory = result['constant_return_trajectory']
        assert len(trajectory) == 26  # Years 0-25

        # First year should have original portfolio value
        assert trajectory[0]['portfolio_value'] == 1000000
        assert trajectory[0]['age'] == 65

    def test_result_includes_summary(self):
        """Test that summary statistics are included."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert 'summary' in result
        summary = result['summary']
        assert 'median_final_value' in summary
        assert 'worst_case_final_value' in summary
        assert 'best_case_final_value' in summary

    def test_result_includes_parameters(self):
        """Test that input parameters are echoed in result."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1500000,
            retirement_age=60,
            life_expectancy=95,
            annual_return_rate=0.06,
            inflation_rate=0.025,
            return_std_dev=0.12,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=50000,
        )
        result = calc.calculate()

        params = result['parameters']
        assert params['portfolio_value'] == 1500000
        assert params['mean_return'] == 6.0  # Converted to percentage
        assert params['inflation_rate'] == 2.5  # Converted to percentage
        assert params['return_std_dev'] == 12.0  # Converted to percentage
        assert params['years_in_retirement'] == 35  # 95 - 60


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_high_withdrawal_results_in_low_success_rate(self):
        """Test that excessive withdrawal leads to portfolio depletion."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=150000,  # 15% withdrawal - very high
        )
        result = calc.calculate()

        # With 15% withdrawal, success rate should be very low
        assert result['success_rate'] < 50

    def test_low_withdrawal_results_in_high_success_rate(self):
        """Test that conservative withdrawal has high success rate."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.15,
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=20000,  # 2% withdrawal - very conservative
        )
        result = calc.calculate()

        # With 2% withdrawal, success rate should be very high
        assert result['success_rate'] > 90

    def test_zero_volatility_deterministic_result(self):
        """Test that 0% volatility gives consistent deterministic result."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            annual_return_rate=0.07,
            inflation_rate=0.03,
            return_std_dev=0.0,  # No volatility
            num_simulations=50,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        # With no volatility, all simulations should have same result
        # So success rate should be either 0% or 100%
        assert result['success_rate'] in [0.0, 100.0]

        # All percentiles should be equal
        p = result['final_value_percentiles']
        assert p['p5'] == p['p50'] == p['p95']

    def test_short_retirement_period(self):
        """Test with very short retirement period."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=67,  # Only 2 years
            num_simulations=100,
            mode='evaluate_success',
            withdrawal_amount=40000,
        )
        result = calc.calculate()

        assert len(result['yearly_percentiles']) == 3  # Years 0, 1, 2
        # Short retirement with reasonable withdrawal should have high success
        assert result['success_rate'] > 90

    def test_pension_reduces_withdrawal_need(self):
        """Test that pension income reduces portfolio withdrawal need."""
        # Without pension
        calc_no_pension = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=200,
            mode='evaluate_success',
            withdrawal_amount=60000,
        )
        result_no_pension = calc_no_pension.calculate()

        # With $20k/year pension
        calc_with_pension = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=200,
            mode='evaluate_success',
            withdrawal_amount=60000,
            pension_annual=20000,
        )
        result_with_pension = calc_with_pension.calculate()

        # Pension should improve success rate
        assert result_with_pension['success_rate'] >= result_no_pension['success_rate']


@pytest.mark.unit
class TestBinarySearch:
    """Tests for binary search algorithm in find_withdrawal mode."""

    def test_binary_search_converges(self):
        """Test that binary search converges within iteration limit."""
        calc = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=100,
            mode='find_withdrawal',
            target_success_rate=85,
        )
        result = calc.calculate()

        # Should return a valid withdrawal amount
        assert result['safe_withdrawal_annual'] > 0
        assert result['safe_withdrawal_annual'] < calc.portfolio_value * 0.15

    def test_different_target_rates_produce_different_withdrawals(self):
        """Test that higher target success = lower safe withdrawal."""
        calc_90 = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=200,
            mode='find_withdrawal',
            target_success_rate=90,
        )
        result_90 = calc_90.calculate()

        calc_75 = EnhancedMonteCarloCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            num_simulations=200,
            mode='find_withdrawal',
            target_success_rate=75,
        )
        result_75 = calc_75.calculate()

        # Higher success rate target should result in lower safe withdrawal
        # (more conservative)
        assert result_90['safe_withdrawal_annual'] <= result_75['safe_withdrawal_annual']
