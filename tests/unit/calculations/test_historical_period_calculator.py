"""
Unit tests for Historical Period Calculator.
"""

import pytest
from decimal import Decimal
from jretirewise.calculations.calculators import HistoricalPeriodCalculator
from jretirewise.calculations.data import (
    SP500_RETURNS, BOND_RETURNS, INFLATION_RATES,
    get_returns_for_period, get_inflation_for_period, get_available_start_years
)


class TestHistoricalDataModule:
    """Test the historical data module."""

    def test_sp500_returns_data_exists(self):
        """Verify S&P 500 data exists for expected years."""
        assert 1960 in SP500_RETURNS
        assert 2024 in SP500_RETURNS
        assert len(SP500_RETURNS) >= 60  # At least 60 years of data

    def test_bond_returns_data_exists(self):
        """Verify bond return data exists."""
        assert 1960 in BOND_RETURNS
        assert 2024 in BOND_RETURNS

    def test_inflation_rates_data_exists(self):
        """Verify inflation data exists."""
        assert 1960 in INFLATION_RATES
        assert 2024 in INFLATION_RATES

    def test_returns_are_reasonable(self):
        """Verify return values are within reasonable bounds."""
        for year, return_val in SP500_RETURNS.items():
            assert -0.50 < return_val < 0.50, f"S&P 500 return for {year} out of bounds"

        for year, return_val in BOND_RETURNS.items():
            assert -0.30 < return_val < 0.40, f"Bond return for {year} out of bounds"

    def test_get_returns_for_period(self):
        """Test getting blended returns for a period."""
        returns = get_returns_for_period(1990, 10, 0.60)
        assert len(returns) == 10
        assert all(isinstance(r, float) for r in returns)

    def test_get_returns_for_period_100_percent_stocks(self):
        """Test 100% stock allocation."""
        returns = get_returns_for_period(2000, 5, 1.0)
        assert len(returns) == 5
        # Should match S&P 500 returns exactly
        for i, r in enumerate(returns):
            assert abs(r - SP500_RETURNS[2000 + i]) < 0.0001

    def test_get_returns_for_period_100_percent_bonds(self):
        """Test 100% bond allocation."""
        returns = get_returns_for_period(2000, 5, 0.0)
        assert len(returns) == 5
        # Should match bond returns exactly
        for i, r in enumerate(returns):
            assert abs(r - BOND_RETURNS[2000 + i]) < 0.0001

    def test_get_inflation_for_period(self):
        """Test getting inflation rates for a period."""
        rates = get_inflation_for_period(1980, 10)
        assert len(rates) == 10
        # 1980 had high inflation
        assert rates[0] > 0.10

    def test_get_available_start_years(self):
        """Test getting available start years."""
        years = get_available_start_years(30)
        assert len(years) > 0
        assert min(years) >= 1960
        assert max(years) <= 2024 - 30 + 1


class TestHistoricalPeriodCalculator:
    """Test the Historical Period Calculator."""

    def test_calculator_initialization(self):
        """Test calculator initializes correctly."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.04,
        )
        assert calc.portfolio_value == 1000000
        assert calc.retirement_age == 65
        assert calc.life_expectancy == 95
        assert calc.withdrawal_rate == 0.04
        assert calc.years_in_retirement == 30

    def test_calculator_with_defaults(self):
        """Test calculator with default parameters."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=60,
            life_expectancy=90,
        )
        assert calc.withdrawal_rate == 0.04
        assert calc.stock_allocation == 0.60

    def test_calculate_returns_expected_keys(self):
        """Test calculate method returns expected keys."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        assert 'calculator_type' in result
        assert result['calculator_type'] == 'historical'
        assert 'success_rate' in result
        assert 'total_periods_tested' in result
        assert 'successful_periods' in result
        assert 'failed_periods' in result
        assert 'best_case' in result
        assert 'worst_case' in result
        assert 'median_case' in result
        assert 'final_value_percentiles' in result
        assert 'yearly_percentiles' in result
        assert 'vulnerable_periods' in result
        assert 'notable_periods' in result
        assert 'period_results' in result
        assert 'parameters' in result

    def test_conservative_withdrawal_rate_succeeds(self):
        """Test that a conservative 3% withdrawal rate has high success."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.03,  # Very conservative
            stock_allocation=0.60,
        )
        result = calc.calculate()

        # 3% should have very high success rate
        assert result['success_rate'] >= 95.0

    def test_aggressive_withdrawal_rate_fails(self):
        """Test that an aggressive 8% withdrawal rate has failures."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=95,  # 30 year retirement
            withdrawal_rate=0.08,  # Very aggressive
            stock_allocation=0.60,
        )
        result = calc.calculate()

        # 8% should have significant failures
        assert result['success_rate'] < 100.0
        assert result['failed_periods'] > 0

    def test_four_percent_rule_reasonable_success(self):
        """Test the traditional 4% rule has reasonable success rate."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.04,
            stock_allocation=0.60,
        )
        result = calc.calculate()

        # 4% rule should have high but not 100% success for 30 years
        assert result['success_rate'] >= 80.0

    def test_best_worst_median_cases_populated(self):
        """Test that best/worst/median cases are populated."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        # Best case should have positive final value
        assert result['best_case']['final_portfolio_value'] > 0
        assert 'start_year' in result['best_case']

        # Worst case should exist
        assert 'start_year' in result['worst_case']
        assert 'years_lasted' in result['worst_case']

        # Median case should exist
        assert 'start_year' in result['median_case']
        assert result['median_case']['final_portfolio_value'] >= 0

    def test_percentiles_calculated(self):
        """Test that percentiles are calculated correctly."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        percentiles = result['final_value_percentiles']
        assert 'p5' in percentiles
        assert 'p50' in percentiles
        assert 'p95' in percentiles

        # Percentiles should be in order
        assert percentiles['p5'] <= percentiles['p25']
        assert percentiles['p25'] <= percentiles['p50']
        assert percentiles['p50'] <= percentiles['p75']
        assert percentiles['p75'] <= percentiles['p95']

    def test_yearly_percentiles_structure(self):
        """Test yearly percentiles have correct structure."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        yearly = result['yearly_percentiles']
        assert len(yearly) > 0

        # Check first year structure
        first_year = yearly[0]
        assert 'year' in first_year
        assert 'age' in first_year
        assert 'p5' in first_year
        assert 'p50' in first_year
        assert 'p95' in first_year
        assert 'mean' in first_year

    def test_notable_periods_analyzed(self):
        """Test that notable historical periods are analyzed."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        notable = result['notable_periods']
        assert len(notable) > 0

        # Check structure
        for period in notable:
            assert 'period_name' in period
            assert 'start_year' in period
            assert 'success' in period
            assert 'final_portfolio_value' in period

    def test_social_security_reduces_failures(self):
        """Test that Social Security income reduces failures."""
        # Without SS
        calc_no_ss = HistoricalPeriodCalculator(
            portfolio_value=800000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.05,
            social_security_start_age=None,
            social_security_annual=0,
        )
        result_no_ss = calc_no_ss.calculate()

        # With SS
        calc_with_ss = HistoricalPeriodCalculator(
            portfolio_value=800000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.05,
            social_security_start_age=67,
            social_security_annual=30000,
        )
        result_with_ss = calc_with_ss.calculate()

        # Success rate should be higher with SS
        assert result_with_ss['success_rate'] >= result_no_ss['success_rate']

    def test_pension_reduces_failures(self):
        """Test that pension income reduces failures."""
        # Without pension
        calc_no_pension = HistoricalPeriodCalculator(
            portfolio_value=800000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.05,
            pension_annual=0,
        )
        result_no_pension = calc_no_pension.calculate()

        # With pension
        calc_with_pension = HistoricalPeriodCalculator(
            portfolio_value=800000,
            retirement_age=65,
            life_expectancy=95,
            withdrawal_rate=0.05,
            pension_annual=20000,
        )
        result_with_pension = calc_with_pension.calculate()

        # Success rate should be higher with pension
        assert result_with_pension['success_rate'] >= result_no_pension['success_rate']

    def test_stock_allocation_affects_results(self):
        """Test that stock allocation affects results."""
        # Low stock allocation
        calc_low = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
            stock_allocation=0.20,
        )
        result_low = calc_low.calculate()

        # High stock allocation
        calc_high = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
            stock_allocation=0.80,
        )
        result_high = calc_high.calculate()

        # Results should be different
        assert result_low['best_case']['final_portfolio_value'] != result_high['best_case']['final_portfolio_value']

    def test_parameters_stored(self):
        """Test that input parameters are stored in result."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1500000,
            retirement_age=60,
            life_expectancy=95,
            withdrawal_rate=0.035,
            stock_allocation=0.70,
        )
        result = calc.calculate()

        params = result['parameters']
        assert params['portfolio_value'] == 1500000
        assert params['retirement_age'] == 60
        assert params['life_expectancy'] == 95
        assert abs(params['withdrawal_rate'] - 3.5) < 0.001  # Stored as percentage
        assert abs(params['stock_allocation'] - 70) < 0.001  # Stored as percentage

    def test_vulnerable_periods_identified(self):
        """Test that vulnerable periods are identified for failing scenarios."""
        # Use aggressive withdrawal to ensure some failures
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=60,
            life_expectancy=100,  # 40 year retirement
            withdrawal_rate=0.06,  # Aggressive
            stock_allocation=0.60,
        )
        result = calc.calculate()

        if result['failed_periods'] > 0:
            vulnerable = result['vulnerable_periods']
            assert len(vulnerable) > 0

            for period in vulnerable:
                assert 'start_year' in period
                assert 'years_lasted' in period
                assert 'shortfall_years' in period
                assert 'reason' in period

    def test_short_retirement_high_success(self):
        """Test that a short retirement period has high success."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=70,
            life_expectancy=85,  # Only 15 years
            withdrawal_rate=0.05,
        )
        result = calc.calculate()

        # Short retirement should have very high success even at 5%
        assert result['success_rate'] >= 90.0

    def test_periods_tested_count_matches(self):
        """Test that period counts are consistent."""
        calc = HistoricalPeriodCalculator(
            portfolio_value=1000000,
            retirement_age=65,
            life_expectancy=90,
            withdrawal_rate=0.04,
        )
        result = calc.calculate()

        total = result['total_periods_tested']
        success = result['successful_periods']
        failed = result['failed_periods']

        assert total == success + failed
        assert len(result['period_results']) == total
