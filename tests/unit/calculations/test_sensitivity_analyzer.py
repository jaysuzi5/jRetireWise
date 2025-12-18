"""
Unit tests for SensitivityAnalyzer.

Tests comprehensive sensitivity analysis functionality including parameter adjustments,
tornado chart generation, and comparison to baseline calculations.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from jretirewise.calculations.sensitivity_analyzer import SensitivityAnalyzer
from jretirewise.scenarios.models import RetirementScenario, CalculationResult
from django.contrib.auth.models import User


class TestSensitivityAnalyzerInitialization:
    """Test suite for SensitivityAnalyzer initialization."""

    def test_initialization_with_valid_scenario(self, mock_scenario_with_result):
        """Test successful initialization with completed scenario."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        assert analyzer.scenario == mock_scenario_with_result
        assert analyzer.baseline_result == mock_scenario_with_result.result
        assert analyzer.calculator_type == '4_percent'
        assert analyzer.baseline_params is not None

    def test_initialization_fails_without_result(self, mock_scenario_no_result):
        """Test initialization fails if scenario has no result."""
        with pytest.raises(ValueError, match="must have a completed calculation result"):
            SensitivityAnalyzer(mock_scenario_no_result)

    def test_initialization_fails_with_pending_result(self, mock_scenario_pending_result):
        """Test initialization fails if result is not completed."""
        with pytest.raises(ValueError, match="must have a completed calculation result"):
            SensitivityAnalyzer(mock_scenario_pending_result)


class TestCalculateWithAdjustment:
    """Test suite for calculate_with_adjustment method."""

    def test_calculate_with_no_adjustments(self, mock_scenario_with_result):
        """Test calculation with zero adjustments returns baseline-like result."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=0.0,
            spending_adjustment=0.0,
            inflation_adjustment=0.0
        )

        assert 'success_rate' in result
        assert 'final_value' in result
        assert 'comparison_to_baseline' in result
        assert result['comparison_to_baseline']['success_rate_delta'] >= -1.0  # Allow small variance

    def test_calculate_with_return_adjustment(self, mock_scenario_with_result):
        """Test calculation with return rate adjustment."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=-0.02,  # -2% return
            spending_adjustment=0.0,
            inflation_adjustment=0.0
        )

        assert result['adjustments']['return_adjustment'] == -0.02
        assert result['parameters_used']['annual_return_rate'] == 0.05  # 7% - 2% = 5%

    def test_calculate_with_spending_adjustment(self, mock_scenario_with_result):
        """Test calculation with spending adjustment."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=0.0,
            spending_adjustment=0.20,  # +20% spending
            inflation_adjustment=0.0
        )

        assert result['adjustments']['spending_adjustment'] == 0.20
        # Spending should be 20% higher: 40000 * 1.20 = 48000
        assert result['parameters_used']['annual_spending'] == 48000.0

    def test_calculate_with_inflation_adjustment(self, mock_scenario_with_result):
        """Test calculation with inflation adjustment."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=0.0,
            spending_adjustment=0.0,
            inflation_adjustment=0.01  # +1% inflation
        )

        assert result['adjustments']['inflation_adjustment'] == 0.01
        assert result['parameters_used']['inflation_rate'] == 0.04  # 3% + 1% = 4%

    def test_calculate_with_multiple_adjustments(self, mock_scenario_with_result):
        """Test calculation with combined adjustments."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=-0.02,
            spending_adjustment=0.10,
            inflation_adjustment=0.01
        )

        assert result['adjustments']['return_adjustment'] == -0.02
        assert result['adjustments']['spending_adjustment'] == 0.10
        assert result['adjustments']['inflation_adjustment'] == 0.01
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] >= 0  # May be 0 for fast calculations

    def test_comparison_to_baseline(self, mock_scenario_with_result):
        """Test comparison metrics to baseline are calculated."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.calculate_with_adjustment(
            return_adjustment=-0.03,  # Significant negative adjustment
            spending_adjustment=0.0,
            inflation_adjustment=0.0
        )

        comparison = result['comparison_to_baseline']
        assert 'success_rate_delta' in comparison
        assert 'final_value_delta' in comparison
        assert 'final_value_percent_change' in comparison

class TestGenerateTornadoData:
    """Test suite for generate_tornado_data method."""

    def test_generate_tornado_data_default_ranges(self, mock_scenario_with_result):
        """Test tornado chart generation with default parameter ranges."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.generate_tornado_data()

        assert 'tornado_data' in result
        assert 'parameter_impacts' in result
        assert len(result['tornado_data']) == 3  # Return, Spending, Inflation

    def test_tornado_data_sorted_by_impact(self, mock_scenario_with_result):
        """Test tornado data is sorted by impact (highest first)."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.generate_tornado_data()

        impacts = [item['impact'] for item in result['tornado_data']]
        assert impacts == sorted(impacts, reverse=True), "Tornado data should be sorted by impact"

    def test_tornado_data_structure(self, mock_scenario_with_result):
        """Test tornado data has correct structure."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.generate_tornado_data()

        for item in result['tornado_data']:
            assert 'parameter' in item
            assert 'low_value' in item
            assert 'high_value' in item
            assert 'impact' in item
            assert 'impact_percent' in item
            assert 'range_tested' in item
            assert 'min' in item['range_tested']
            assert 'max' in item['range_tested']
            assert 'step' in item['range_tested']

    def test_tornado_data_custom_ranges(self, mock_scenario_with_result):
        """Test tornado chart with custom parameter ranges."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result = analyzer.generate_tornado_data(
            return_range=(-0.03, 0.03, 0.01),
            spending_range=(0.0, 0.30, 0.10),
            inflation_range=(0.0, 0.02, 0.01)
        )

        assert len(result['tornado_data']) == 3
        # Verify custom ranges are used
        return_item = next(item for item in result['tornado_data'] if item['parameter'] == 'Return Rate')
        assert return_item['range_tested']['min'] == -0.03
        assert return_item['range_tested']['max'] == 0.03


class TestParameterImpact:
    """Test suite for _test_parameter_impact method."""

    def test_return_rate_impact(self, mock_scenario_with_result):
        """Test return rate parameter impact calculation."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)
        baseline_success_rate = 100.0

        impact = analyzer._test_parameter_impact(
            'return',
            (-0.02, 0.02, 0.01),
            baseline_success_rate
        )

        assert 'low_value' in impact
        assert 'high_value' in impact
        assert 'impact' in impact
        assert 'impact_percent' in impact
        assert impact['impact'] >= 0  # Impact should be positive (absolute value)

    def test_spending_impact(self, mock_scenario_with_result):
        """Test spending parameter impact calculation."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)
        baseline_success_rate = 100.0

        impact = analyzer._test_parameter_impact(
            'spending',
            (0.0, 0.40, 0.10),
            baseline_success_rate
        )

        assert impact['impact'] >= 0
        assert impact['range_tested']['min'] == 0.0
        assert impact['range_tested']['max'] == 0.40

    def test_inflation_impact(self, mock_scenario_with_result):
        """Test inflation parameter impact calculation."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)
        baseline_success_rate = 100.0

        impact = analyzer._test_parameter_impact(
            'inflation',
            (0.0, 0.03, 0.01),
            baseline_success_rate
        )

        assert impact['impact'] >= 0
        assert impact['range_tested']['min'] == 0.0
        assert impact['range_tested']['max'] == 0.03


class TestApplyAdjustments:
    """Test suite for _apply_adjustments method."""

    def test_apply_return_adjustment(self, mock_scenario_with_result):
        """Test applying return rate adjustment to parameters."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        adjusted = analyzer._apply_adjustments(
            return_adjustment=-0.02,
            spending_adjustment=0.0,
            inflation_adjustment=0.0
        )

        assert adjusted['annual_return_rate'] == 0.05  # 7% - 2%

    def test_apply_spending_adjustment(self, mock_scenario_with_result):
        """Test applying spending adjustment (multiplicative)."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        adjusted = analyzer._apply_adjustments(
            return_adjustment=0.0,
            spending_adjustment=0.20,  # +20%
            inflation_adjustment=0.0
        )

        assert adjusted['annual_spending'] == 48000.0  # 40000 * 1.20

    def test_apply_inflation_adjustment(self, mock_scenario_with_result):
        """Test applying inflation adjustment to parameters."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        adjusted = analyzer._apply_adjustments(
            return_adjustment=0.0,
            spending_adjustment=0.0,
            inflation_adjustment=0.01
        )

        assert adjusted['inflation_rate'] == 0.04  # 3% + 1%

    def test_apply_all_adjustments(self, mock_scenario_with_result):
        """Test applying all adjustments simultaneously."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        adjusted = analyzer._apply_adjustments(
            return_adjustment=-0.01,
            spending_adjustment=0.10,
            inflation_adjustment=0.005
        )

        assert pytest.approx(adjusted['annual_return_rate'], abs=0.001) == 0.06  # 7% - 1%
        assert adjusted['annual_spending'] == 44000.0  # 40000 * 1.10
        assert pytest.approx(adjusted['inflation_rate'], abs=0.001) == 0.035  # 3% + 0.5%


class TestCreateCalculator:
    """Test suite for _create_calculator method."""

    def test_create_four_percent_calculator(self, mock_scenario_with_result):
        """Test creating 4% rule calculator instance."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        params = analyzer.baseline_params.copy()
        calculator = analyzer._create_calculator(params)

        assert calculator is not None
        assert calculator.__class__.__name__ == 'FourPercentCalculator'

    def test_create_four_point_seven_percent_calculator(self, mock_scenario_47_percent):
        """Test creating 4.7% rule calculator instance."""
        analyzer = SensitivityAnalyzer(mock_scenario_47_percent)

        params = analyzer.baseline_params.copy()
        calculator = analyzer._create_calculator(params)

        assert calculator is not None
        assert calculator.__class__.__name__ == 'FourPointSevenPercentCalculator'

    def test_create_monte_carlo_calculator(self, mock_monte_carlo_scenario):
        """Test creating Monte Carlo calculator instance."""
        analyzer = SensitivityAnalyzer(mock_monte_carlo_scenario)

        params = analyzer.baseline_params.copy()
        calculator = analyzer._create_calculator(params)

        assert calculator is not None
        assert calculator.__class__.__name__ == 'EnhancedMonteCarloCalculator'

    def test_create_calculator_with_annual_return_variant(self, mock_scenario_with_annual_return):
        """Test handling 'annual_return' parameter name variant."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_annual_return)

        params = analyzer.baseline_params.copy()
        calculator = analyzer._create_calculator(params)

        assert calculator is not None
        assert calculator.annual_return_rate == Decimal('0.07')

    def test_create_calculator_unsupported_type(self, mock_scenario_unsupported_type):
        """Test error handling for unsupported calculator types."""
        analyzer = SensitivityAnalyzer.__new__(SensitivityAnalyzer)
        analyzer.scenario = mock_scenario_unsupported_type
        analyzer.calculator_type = 'historical'
        analyzer.baseline_params = {}

        with pytest.raises(ValueError, match="Sensitivity analysis not supported"):
            analyzer._create_calculator(analyzer.baseline_params)


class TestExtractMetrics:
    """Test suite for _extract_metrics method."""

    def test_extract_metrics_with_success_rate(self, mock_scenario_with_result):
        """Test extracting metrics when success_rate is at top level."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {
            'success_rate': 95.5,
            'projections': [
                {'portfolio_value': 800000, 'annual_withdrawal': 40000},
                {'portfolio_value': 600000, 'annual_withdrawal': 40000},
            ]
        }

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['success_rate'] == 95.5
        assert metrics['final_value'] == 600000
        assert metrics['withdrawal_amount'] == 40000

    def test_extract_metrics_with_summary(self, mock_scenario_with_result):
        """Test extracting metrics when data is in summary dict."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {
            'summary': {
                'success_rate': 88.0
            },
            'projections': [
                {'portfolio_value': 1000000, 'annual_withdrawal': 50000},
                {'portfolio_value': 750000, 'annual_withdrawal': 50000},
            ]
        }

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['success_rate'] == 88.0
        assert metrics['final_value'] == 750000

    def test_extract_metrics_with_percentiles(self, mock_scenario_with_result):
        """Test extracting metrics from Monte Carlo percentiles."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {
            'success_rate': 92.3,
            'final_value_percentiles': {
                'p10': 200000,
                'p50': 800000,
                'p90': 1500000
            },
            'withdrawal_annual': 45000
        }

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['success_rate'] == 92.3
        assert metrics['final_value'] == 800000  # Median (p50)
        assert metrics['withdrawal_amount'] == 45000

    def test_extract_metrics_with_safe_withdrawal(self, mock_scenario_with_result):
        """Test extracting withdrawal from safe_withdrawal_annual field."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {
            'success_rate': 90.0,
            'safe_withdrawal_annual': 42000,
            'projections': [
                {'portfolio_value': 1000000},
            ]
        }

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['withdrawal_amount'] == 42000

    def test_extract_metrics_with_years_to_depletion(self, mock_scenario_with_result):
        """Test extracting years to depletion when present."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {
            'success_rate': 75.0,
            'depletion_stats': {
                'median_year': 25,
                'p10_year': 18,
                'p90_year': 32
            },
            'projections': [
                {'portfolio_value': 500000},
            ]
        }

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['years_to_depletion'] == 25

    def test_extract_metrics_default_values(self, mock_scenario_with_result):
        """Test default values when metrics are missing."""
        analyzer = SensitivityAnalyzer(mock_scenario_with_result)

        result_data = {}

        metrics = analyzer._extract_metrics(result_data)

        assert metrics['success_rate'] == 100.0  # Default for deterministic
        assert metrics['final_value'] == 0.0
        assert metrics['withdrawal_amount'] == 0.0
        assert metrics['years_to_depletion'] is None


# Pytest Fixtures

@pytest.fixture
def mock_user():
    """Create a mock user with financial profile."""
    user = Mock(spec=User)
    user.financial_profile = Mock()
    user.financial_profile.current_portfolio_value = Decimal('1000000')
    user.financial_profile.annual_spending = Decimal('40000')
    user.financial_profile.current_age = 60
    user.financial_profile.retirement_age = 65
    user.financial_profile.life_expectancy = 95
    return user


@pytest.fixture
def mock_scenario_with_result(mock_user):
    """Create a mock scenario with completed result."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = '4_percent'
    scenario.parameters = {
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

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {
        'calculation': {
            'success_rate': 100.0,
            'projections': [
                {'portfolio_value': 1000000, 'annual_withdrawal': 40000},
                {'portfolio_value': 950000, 'annual_withdrawal': 40000},
            ]
        }
    }

    scenario.result = result
    return scenario


@pytest.fixture
def mock_scenario_no_result(mock_user):
    """Create a mock scenario without a result."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = '4_percent'
    scenario.parameters = {}
    scenario.result = None
    return scenario


@pytest.fixture
def mock_scenario_pending_result(mock_user):
    """Create a mock scenario with pending result."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = '4_percent'
    scenario.parameters = {}

    result = Mock(spec=CalculationResult)
    result.status = 'pending'

    scenario.result = result
    return scenario


@pytest.fixture
def mock_monte_carlo_scenario(mock_user):
    """Create a mock Monte Carlo scenario."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = 'monte_carlo'
    scenario.parameters = {
        'portfolio_value': 1000000,
        'annual_spending': 40000,
        'retirement_age': 65,
        'life_expectancy': 95,
        'annual_return_rate': 0.07,
        'inflation_rate': 0.03,
        'return_std_dev': 0.15,
        'num_simulations': 1000,
        'mode': 'evaluate_success',
        'withdrawal_amount': 40000,
        'target_success_rate': 90.0,
        'social_security_annual': 0,
        'social_security_start_age': 67,
        'pension_annual': 0,
        'pension_start_age': 65,
        'periods_per_year': 12,
    }

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {
        'calculation': {
            'success_rate': 92.5,
            'final_value_percentiles': {'p50': 850000},
            'withdrawal_annual': 40000,
        }
    }

    scenario.result = result
    return scenario


@pytest.fixture
def mock_scenario_unsupported_type(mock_user):
    """Create a mock scenario with unsupported calculator type."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = 'historical'
    scenario.parameters = {}

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {'calculation': {}}

    scenario.result = result
    return scenario


@pytest.fixture
def mock_scenario_47_percent(mock_user):
    """Create a mock scenario with 4.7% calculator."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = '4_7_percent'
    scenario.parameters = {
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

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {
        'calculation': {
            'success_rate': 100.0,
            'projections': [
                {'portfolio_value': 1000000, 'annual_withdrawal': 47000},
                {'portfolio_value': 960000, 'annual_withdrawal': 47000},
            ]
        }
    }

    scenario.result = result
    return scenario


@pytest.fixture
def mock_scenario_with_annual_return(mock_user):
    """Create a mock scenario using 'annual_return' parameter name variant."""
    scenario = Mock(spec=RetirementScenario)
    scenario.user = mock_user
    scenario.calculator_type = '4_percent'
    scenario.parameters = {
        'portfolio_value': 1000000,
        'annual_spending': 40000,
        'current_age': 60,
        'retirement_age': 65,
        'life_expectancy': 95,
        'annual_return': 0.07,  # Note: using 'annual_return' instead of 'annual_return_rate'
        'inflation_rate': 0.03,
        'social_security_annual': 0,
        'social_security_start_age': 67,
        'pension_annual': 0,
        'pension_start_age': 65,
    }

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {
        'calculation': {
            'success_rate': 100.0,
            'projections': [
                {'portfolio_value': 1000000},
            ]
        }
    }

    scenario.result = result
    return scenario


@pytest.fixture
def mock_scenario_no_profile(mock_user):
    """Create a mock scenario where user has no financial profile."""
    user = Mock(spec=User)
    # Simulate missing financial_profile attribute
    type(user).financial_profile = Mock(side_effect=AttributeError("User has no financial profile"))

    scenario = Mock(spec=RetirementScenario)
    scenario.user = user
    scenario.calculator_type = '4_percent'
    scenario.parameters = {
        'portfolio_value': 1000000,
        'annual_spending': 40000,
        'retirement_age': 65,
        'life_expectancy': 95,
    }

    result = Mock(spec=CalculationResult)
    result.status = 'completed'
    result.result_data = {'calculation': {}}

    scenario.result = result
    return scenario
