"""
Sensitivity Analysis Calculator.

This module provides functionality to perform sensitivity analysis on existing retirement scenarios.
It allows testing how changes in key parameters (returns, spending, inflation) affect retirement outcomes.
"""

import time
from typing import Dict, List, Tuple, Any
from decimal import Decimal

from jretirewise.scenarios.models import RetirementScenario, CalculationResult
from jretirewise.calculations.calculators import (
    FourPercentCalculator,
    FourPointSevenPercentCalculator,
    EnhancedMonteCarloCalculator,
    HistoricalPeriodCalculator,
)


class SensitivityAnalyzer:
    """
    Performs sensitivity analysis on retirement scenarios by adjusting parameters
    and comparing results to baseline.
    """

    def __init__(self, scenario: RetirementScenario):
        """
        Initialize the sensitivity analyzer with a baseline scenario.

        Args:
            scenario: The baseline RetirementScenario to analyze
        """
        self.scenario = scenario
        self.baseline_result = scenario.result

        if not self.baseline_result or self.baseline_result.status != 'completed':
            raise ValueError("Scenario must have a completed calculation result")

        self.baseline_params = scenario.parameters or {}
        self.calculator_type = scenario.calculator_type

    def calculate_with_adjustment(
        self,
        return_adjustment: float = 0.0,
        spending_adjustment: float = 0.0,
        inflation_adjustment: float = 0.0
    ) -> Dict[str, Any]:
        """
        Run calculation with parameter adjustments and compare to baseline.

        Args:
            return_adjustment: Adjustment to annual return rate (e.g., -0.02 for -2%)
            spending_adjustment: Adjustment to spending (e.g., 0.20 for +20%)
            inflation_adjustment: Adjustment to inflation rate (e.g., 0.01 for +1%)

        Returns:
            Dictionary containing adjusted results and comparison to baseline:
            {
                'success_rate': float,
                'final_value': float,
                'years_to_depletion': int|null,
                'withdrawal_amount': float,
                'comparison_to_baseline': {
                    'success_rate_delta': float,
                    'final_value_delta': float,
                    'final_value_percent_change': float
                },
                'parameters_used': {...}
            }
        """
        start_time = time.time()

        # Get adjusted parameters
        adjusted_params = self._apply_adjustments(
            return_adjustment,
            spending_adjustment,
            inflation_adjustment
        )

        # Run calculator with adjusted parameters
        calculator = self._create_calculator(adjusted_params)
        result = calculator.calculate()

        # Extract metrics from result
        metrics = self._extract_metrics(result)

        # Compare to baseline
        baseline_metrics = self._extract_metrics(
            self.baseline_result.result_data.get('calculation', {})
        )

        comparison = {
            'success_rate_delta': metrics['success_rate'] - baseline_metrics['success_rate'],
            'final_value_delta': metrics['final_value'] - baseline_metrics['final_value'],
            'final_value_percent_change': (
                ((metrics['final_value'] - baseline_metrics['final_value']) / baseline_metrics['final_value'] * 100)
                if baseline_metrics['final_value'] > 0 else 0
            )
        }

        execution_time_ms = int((time.time() - start_time) * 1000)

        return {
            **metrics,
            'comparison_to_baseline': comparison,
            'parameters_used': adjusted_params,
            'adjustments': {
                'return_adjustment': return_adjustment,
                'spending_adjustment': spending_adjustment,
                'inflation_adjustment': inflation_adjustment
            },
            'execution_time_ms': execution_time_ms
        }

    def generate_tornado_data(
        self,
        return_range: Tuple[float, float, float] = (-0.05, 0.05, 0.01),
        spending_range: Tuple[float, float, float] = (0.0, 0.50, 0.10),
        inflation_range: Tuple[float, float, float] = (0.0, 0.04, 0.01)
    ) -> Dict[str, Any]:
        """
        Generate tornado chart data by testing one parameter at a time.

        Args:
            return_range: (min, max, step) for return rate adjustment
            spending_range: (min, max, step) for spending adjustment
            inflation_range: (min, max, step) for inflation adjustment

        Returns:
            Dictionary containing tornado chart data and parameter impacts:
            {
                'tornado_data': [
                    {
                        'parameter': 'Return Rate',
                        'low_value': float,
                        'high_value': float,
                        'impact': float,  # absolute impact on success rate
                        'impact_percent': float  # percentage impact
                    },
                    ...
                ],
                'parameter_impacts': {
                    'return': {...},
                    'spending': {...},
                    'inflation': {...}
                }
            }
        """
        baseline_metrics = self._extract_metrics(
            self.baseline_result.result_data.get('calculation', {})
        )
        baseline_success_rate = baseline_metrics['success_rate']

        impacts = []

        # Test return rate impact
        return_impact = self._test_parameter_impact(
            'return',
            return_range,
            baseline_success_rate
        )
        impacts.append({
            'parameter': 'Return Rate',
            **return_impact
        })

        # Test spending impact
        spending_impact = self._test_parameter_impact(
            'spending',
            spending_range,
            baseline_success_rate
        )
        impacts.append({
            'parameter': 'Spending',
            **spending_impact
        })

        # Test inflation impact
        inflation_impact = self._test_parameter_impact(
            'inflation',
            inflation_range,
            baseline_success_rate
        )
        impacts.append({
            'parameter': 'Inflation',
            **inflation_impact
        })

        # Sort by absolute impact (highest first)
        impacts.sort(key=lambda x: abs(x['impact']), reverse=True)

        return {
            'tornado_data': impacts,
            'parameter_impacts': {
                'return': return_impact,
                'spending': spending_impact,
                'inflation': inflation_impact
            }
        }

    def _test_parameter_impact(
        self,
        parameter_name: str,
        param_range: Tuple[float, float, float],
        baseline_success_rate: float
    ) -> Dict[str, Any]:
        """
        Test the impact of a single parameter across its range.

        Args:
            parameter_name: 'return', 'spending', or 'inflation'
            param_range: (min, max, step) for the parameter
            baseline_success_rate: Baseline success rate for comparison

        Returns:
            Dictionary with low/high values and calculated impact
        """
        min_val, max_val, step = param_range

        # Test minimum value
        if parameter_name == 'return':
            low_result = self.calculate_with_adjustment(return_adjustment=min_val)
        elif parameter_name == 'spending':
            low_result = self.calculate_with_adjustment(spending_adjustment=min_val)
        else:  # inflation
            low_result = self.calculate_with_adjustment(inflation_adjustment=min_val)

        # Test maximum value
        if parameter_name == 'return':
            high_result = self.calculate_with_adjustment(return_adjustment=max_val)
        elif parameter_name == 'spending':
            high_result = self.calculate_with_adjustment(spending_adjustment=max_val)
        else:  # inflation
            high_result = self.calculate_with_adjustment(inflation_adjustment=max_val)

        low_success = low_result['success_rate']
        high_success = high_result['success_rate']

        # Calculate impact (range of success rate change)
        impact = abs(high_success - low_success)

        # Calculate percentage impact relative to baseline
        impact_percent = (impact / baseline_success_rate * 100) if baseline_success_rate > 0 else 0

        return {
            'low_value': low_success,
            'high_value': high_success,
            'impact': impact,
            'impact_percent': impact_percent,
            'range_tested': {
                'min': min_val,
                'max': max_val,
                'step': step
            }
        }

    def _apply_adjustments(
        self,
        return_adjustment: float,
        spending_adjustment: float,
        inflation_adjustment: float
    ) -> Dict[str, Any]:
        """
        Apply parameter adjustments to baseline parameters.

        Args:
            return_adjustment: Adjustment to return rate
            spending_adjustment: Adjustment to spending (multiplier, e.g., 0.20 = +20%)
            inflation_adjustment: Adjustment to inflation rate

        Returns:
            Dictionary of adjusted parameters
        """
        params = self.baseline_params.copy()

        # Adjust return rate
        if 'annual_return_rate' in params:
            baseline_return = float(params['annual_return_rate'])
            params['annual_return_rate'] = baseline_return + return_adjustment
        elif 'annual_return' in params:
            baseline_return = float(params['annual_return'])
            params['annual_return'] = baseline_return + return_adjustment

        # Adjust spending
        if 'annual_spending' in params:
            baseline_spending = float(params['annual_spending'])
            params['annual_spending'] = baseline_spending * (1 + spending_adjustment)

        if 'withdrawal_amount' in params:
            baseline_withdrawal = float(params['withdrawal_amount'])
            params['withdrawal_amount'] = baseline_withdrawal * (1 + spending_adjustment)

        # Adjust inflation rate
        if 'inflation_rate' in params:
            baseline_inflation = float(params['inflation_rate'])
            params['inflation_rate'] = baseline_inflation + inflation_adjustment

        return params

    def _create_calculator(self, parameters: Dict[str, Any]):
        """
        Create the appropriate calculator instance based on scenario type.

        Args:
            parameters: Adjusted parameters for the calculation

        Returns:
            Calculator instance
        """
        # Get user profile data
        try:
            financial_profile = self.scenario.user.financial_profile
        except:
            raise ValueError("User must have a financial profile")

        # Extract common parameters
        portfolio_value = float(parameters.get('portfolio_value', financial_profile.current_portfolio_value))
        annual_spending = float(parameters.get('annual_spending', financial_profile.annual_spending))
        current_age = float(parameters.get('current_age', financial_profile.current_age))
        retirement_age = float(parameters.get('retirement_age', financial_profile.retirement_age))
        life_expectancy = int(parameters.get('life_expectancy', financial_profile.life_expectancy))

        annual_return_rate = float(parameters.get('annual_return_rate') or parameters.get('annual_return', 0.07))
        inflation_rate = float(parameters.get('inflation_rate', 0.03))

        # Social Security and Pension
        social_security_annual = float(parameters.get('social_security_annual', 0))
        social_security_start_age = int(parameters.get('social_security_start_age', 67))
        pension_annual = float(parameters.get('pension_annual', 0))
        pension_start_age = int(parameters.get('pension_start_age', retirement_age))

        # Create calculator based on type
        if self.calculator_type == '4_percent':
            return FourPercentCalculator(
                portfolio_value=portfolio_value,
                annual_spending=annual_spending,
                current_age=current_age,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
                social_security_annual=social_security_annual,
                social_security_claiming_age=social_security_start_age,
            )
        elif self.calculator_type == '4_7_percent':
            return FourPointSevenPercentCalculator(
                portfolio_value=portfolio_value,
                annual_spending=annual_spending,
                current_age=current_age,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
                social_security_annual=social_security_annual,
                social_security_claiming_age=social_security_start_age,
            )
        elif self.calculator_type == 'monte_carlo':
            return_std_dev = float(parameters.get('return_std_dev', 0.15))
            num_simulations = int(parameters.get('num_simulations', 1000))
            mode = parameters.get('mode', 'evaluate_success')
            target_success_rate = float(parameters.get('target_success_rate', 90.0))
            withdrawal_amount = parameters.get('withdrawal_amount', annual_spending)
            if withdrawal_amount is not None:
                withdrawal_amount = float(withdrawal_amount)

            social_security_monthly = social_security_annual / 12
            periods_per_year = int(parameters.get('periods_per_year', 12))

            return EnhancedMonteCarloCalculator(
                portfolio_value=portfolio_value,
                retirement_age=int(retirement_age),
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
                return_std_dev=return_std_dev,
                num_simulations=num_simulations,
                mode=mode,
                withdrawal_amount=withdrawal_amount,
                target_success_rate=target_success_rate,
                social_security_start_age=social_security_start_age,
                social_security_monthly_benefit=social_security_monthly,
                pension_annual=pension_annual,
                pension_start_age=pension_start_age,
                periods_per_year=periods_per_year,
            )
        else:
            raise ValueError(f"Sensitivity analysis not supported for calculator type: {self.calculator_type}")

    def _extract_metrics(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics from calculation result.

        Args:
            result_data: Calculation result data

        Returns:
            Dictionary with extracted metrics
        """
        # Handle different result structures
        if 'success_rate' in result_data:
            success_rate = float(result_data['success_rate'])
        elif 'summary' in result_data and 'success_rate' in result_data['summary']:
            success_rate = float(result_data['summary']['success_rate'])
        else:
            success_rate = 100.0  # Default for deterministic calculators

        # Extract final value
        if 'final_value_percentiles' in result_data:
            final_value = float(result_data['final_value_percentiles'].get('p50', 0))
        elif 'projections' in result_data and len(result_data['projections']) > 0:
            final_value = float(result_data['projections'][-1].get('portfolio_value', 0))
        else:
            final_value = 0.0

        # Extract withdrawal amount
        if 'withdrawal_annual' in result_data:
            withdrawal_amount = float(result_data['withdrawal_annual'])
        elif 'safe_withdrawal_annual' in result_data:
            withdrawal_amount = float(result_data['safe_withdrawal_annual'])
        elif 'projections' in result_data and len(result_data['projections']) > 0:
            withdrawal_amount = float(result_data['projections'][0].get('annual_withdrawal', 0))
        else:
            withdrawal_amount = 0.0

        # Years to depletion
        years_to_depletion = None
        if 'depletion_stats' in result_data and result_data['depletion_stats']:
            years_to_depletion = result_data['depletion_stats'].get('median_year')

        return {
            'success_rate': success_rate,
            'final_value': final_value,
            'withdrawal_amount': withdrawal_amount,
            'years_to_depletion': years_to_depletion
        }
