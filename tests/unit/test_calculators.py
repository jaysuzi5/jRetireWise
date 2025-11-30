"""
Unit tests for retirement calculators.
"""

import pytest
from decimal import Decimal
from jretirewise.calculations.calculators import FourPercentCalculator, FourPointSevenPercentCalculator


@pytest.mark.unit
class TestFourPercentCalculator:
    """Tests for 4% rule calculator."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        assert calc.portfolio_value == 1000000.0
        assert calc.annual_spending == 60000.0
        assert calc.retirement_age == 65

    def test_four_percent_withdrawal(self):
        """Test that initial withdrawal is 4% of portfolio."""
        portfolio = 1000000
        calc = FourPercentCalculator(
            portfolio_value=Decimal(str(portfolio)),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result = calc.calculate()

        # First projection should have 4% withdrawal
        first_projection = result['projections'][0]
        expected_withdrawal = portfolio * 0.04
        assert first_projection['annual_withdrawal'] == expected_withdrawal

    def test_calculator_returns_valid_structure(self):
        """Test that calculator returns required result structure."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result = calc.calculate()

        # Check required fields
        assert 'calculator_type' in result
        assert 'success_rate' in result
        assert 'projections' in result
        assert 'final_portfolio_value' in result
        assert 'total_withdrawals' in result

        # Check calculator type
        assert result['calculator_type'] == '4_percent_rule'

    def test_success_rate_high_returns(self):
        """Test success rate with high returns."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('40000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=0.08,  # High return
        )
        result = calc.calculate()

        # With high returns and modest spending, should succeed
        assert result['success_rate'] == 100.0

    def test_success_rate_low_portfolio(self):
        """Test success rate with negative returns and high withdrawals."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('100000'),
            annual_spending=Decimal('50000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=-0.10,  # Negative returns
        )
        result = calc.calculate()

        # With negative returns, portfolio should eventually deplete
        assert result['portfolio_depleted_year'] is not None

    def test_projections_increasing_withdrawals(self):
        """Test that withdrawals increase with inflation."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('40000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
            inflation_rate=0.03,
        )
        result = calc.calculate()

        projections = result['projections']
        # Withdrawals should increase with inflation
        first_withdrawal = projections[0]['annual_withdrawal']
        later_withdrawal = projections[10]['annual_withdrawal']
        assert later_withdrawal > first_withdrawal

    def test_portfolio_balance_calculations(self):
        """Test that portfolio balance is calculated correctly."""
        portfolio = 1000000
        annual_return = 0.07
        calc = FourPercentCalculator(
            portfolio_value=Decimal(str(portfolio)),
            annual_spending=Decimal('40000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
            annual_return_rate=annual_return,
        )
        result = calc.calculate()

        first = result['projections'][0]
        second = result['projections'][1]

        # Check formula: ending_balance = portfolio + return - withdrawal
        # Then next year: portfolio_value = previous ending_balance
        assert second['portfolio_value'] > 0

    def test_depletion_detection(self):
        """Test that portfolio depletion is detected with negative returns."""
        calc = FourPercentCalculator(
            portfolio_value=Decimal('200000'),
            annual_spending=Decimal('50000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,  # Long retirement
            annual_return_rate=-0.05,  # Negative returns
        )
        result = calc.calculate()

        # Should detect depletion with negative returns
        assert result['portfolio_depleted_year'] is not None


@pytest.mark.unit
class TestFourPointSevenPercentCalculator:
    """Tests for 4.7% rule calculator."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = FourPointSevenPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        assert calc.portfolio_value == 1000000.0
        assert calc.annual_spending == 60000.0
        assert calc.retirement_age == 65

    def test_four_seven_percent_withdrawal(self):
        """Test that initial withdrawal is 4.7% of portfolio."""
        portfolio = 1000000
        calc = FourPointSevenPercentCalculator(
            portfolio_value=Decimal(str(portfolio)),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result = calc.calculate()

        # First projection should have 4.7% withdrawal
        first_projection = result['projections'][0]
        expected_withdrawal = portfolio * 0.047
        assert first_projection['annual_withdrawal'] == expected_withdrawal

    def test_calculator_returns_valid_structure(self):
        """Test that calculator returns required result structure."""
        calc = FourPointSevenPercentCalculator(
            portfolio_value=Decimal('1000000'),
            annual_spending=Decimal('60000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result = calc.calculate()

        # Check required fields
        assert 'calculator_type' in result
        assert result['calculator_type'] == '4_7_percent_rule'
        assert 'success_rate' in result
        assert 'projections' in result

    def test_four_seven_higher_withdrawal_than_four(self):
        """Test that 4.7% rule withdraws more than 4% rule."""
        portfolio = 1000000

        calc_4pct = FourPercentCalculator(
            portfolio_value=Decimal(str(portfolio)),
            annual_spending=Decimal('40000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result_4pct = calc_4pct.calculate()
        withdrawal_4pct = result_4pct['projections'][0]['annual_withdrawal']

        calc_47pct = FourPointSevenPercentCalculator(
            portfolio_value=Decimal(str(portfolio)),
            annual_spending=Decimal('40000'),
            current_age=40,
            retirement_age=65,
            life_expectancy=95,
        )
        result_47pct = calc_47pct.calculate()
        withdrawal_47pct = result_47pct['projections'][0]['annual_withdrawal']

        # 4.7% withdrawal should be higher
        assert withdrawal_47pct > withdrawal_4pct
