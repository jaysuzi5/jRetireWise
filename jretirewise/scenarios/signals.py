"""
Signal handlers for scenario calculations.
"""

import time
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import RetirementScenario, CalculationResult
from jretirewise.calculations.calculators import FourPercentCalculator, FourPointSevenPercentCalculator, MonteCarloCalculator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=RetirementScenario)
def run_scenario_calculation(sender, instance, created, **kwargs):
    """
    Automatically run calculation when a scenario is created or updated.
    """
    # Always run calculation (for both creation and updates)

    try:
        # Get or create calculation result
        result, _ = CalculationResult.objects.get_or_create(scenario=instance)
        result.status = 'pending'
        result.save()

        # Extract parameters from scenario
        parameters = instance.parameters or {}

        # Get financial profile - required for fallback values
        try:
            financial_profile = instance.user.financial_profile
        except:
            result.status = 'failed'
            result.error_message = 'User has not completed their financial profile. Please fill out your financial profile first.'
            result.save()
            return

        # Get portfolio value - prefer user's portfolio from the portfolio screens
        # Fall back to financial profile if portfolio doesn't exist
        try:
            user_portfolio = instance.user.portfolio
            portfolio_value = float(user_portfolio.get_total_value())
        except:
            portfolio_value = float(parameters.get('portfolio_value', financial_profile.current_portfolio_value))

        # Use scenario parameters or fall back to user's financial profile
        annual_spending = float(parameters.get('annual_spending', financial_profile.annual_spending))
        # Keep decimal precision for ages instead of converting to int
        current_age = float(parameters.get('current_age', financial_profile.current_age))
        retirement_age = float(parameters.get('retirement_age', financial_profile.retirement_age))
        life_expectancy = int(parameters.get('life_expectancy', financial_profile.life_expectancy))

        # Optional parameters with defaults
        # For annual return rate: try to use portfolio's weighted growth rate, then fallback to parameter or 7%
        annual_return_rate = 0.07  # Default fallback
        if parameters.get('annual_return_rate') or parameters.get('annual_return'):
            annual_return_rate = float(parameters.get('annual_return_rate') or parameters.get('annual_return'))
        else:
            # Try to get weighted growth rate from portfolio by calculating it from accounts
            try:
                user_portfolio = instance.user.portfolio
                accounts = user_portfolio.accounts.filter(status='active')
                portfolio_total_value = sum(float(acc.current_value) for acc in accounts) if accounts else 0

                if portfolio_total_value > 0:
                    # Calculate weighted average growth rate from accounts
                    weighted_growth = sum(
                        float(acc.default_growth_rate) * (float(acc.current_value) / portfolio_total_value)
                        for acc in accounts if acc.current_value > 0
                    )
                    if weighted_growth > 0:
                        annual_return_rate = weighted_growth  # Already in decimal form (0.0347 for 3.47%)
            except:
                pass  # Use default 0.07

        inflation_rate = float(parameters.get('inflation_rate', 0.03))

        # Track which values came from parameters vs defaults for display
        values_used = {
            'portfolio_value': parameters.get('portfolio_value') is not None,
            'annual_spending': parameters.get('annual_spending') is not None,
            'current_age': parameters.get('current_age') is not None,
            'retirement_age': parameters.get('retirement_age') is not None,
            'life_expectancy': parameters.get('life_expectancy') is not None,
            'annual_return_rate': (parameters.get('annual_return_rate') or parameters.get('annual_return')) is not None,
            'inflation_rate': parameters.get('inflation_rate') is not None,
        }

        # Create a defaults dict showing which values were filled in from defaults (not user-provided)
        defaults_used = {
            'portfolio_value': portfolio_value if not values_used['portfolio_value'] else None,
            'annual_spending': annual_spending if not values_used['annual_spending'] else None,
            'current_age': current_age if not values_used['current_age'] else None,
            'retirement_age': retirement_age if not values_used['retirement_age'] else None,
            'life_expectancy': life_expectancy if not values_used['life_expectancy'] else None,
            'annual_return_rate': annual_return_rate if not values_used['annual_return_rate'] else None,
            'inflation_rate': inflation_rate if not values_used['inflation_rate'] else None,
        }

        # Convert annual_return_rate from decimal to percentage for display (0.07 -> 7.0)
        if defaults_used['annual_return_rate'] is not None:
            defaults_used['annual_return_rate'] = float(defaults_used['annual_return_rate']) * 100

        # Convert inflation_rate from decimal to percentage for display (0.03 -> 3.0)
        if defaults_used['inflation_rate'] is not None:
            defaults_used['inflation_rate'] = float(defaults_used['inflation_rate']) * 100

        # Time the calculation
        start_time = time.time()

        # Run the appropriate calculator
        if instance.calculator_type == '4_percent':
            calculator = FourPercentCalculator(
                portfolio_value=portfolio_value,
                annual_spending=annual_spending,
                current_age=current_age,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
            )
        elif instance.calculator_type == '4_7_percent':
            calculator = FourPointSevenPercentCalculator(
                portfolio_value=portfolio_value,
                annual_spending=annual_spending,
                current_age=current_age,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
            )
        elif instance.calculator_type == 'monte_carlo':
            # Get Monte Carlo specific parameters
            return_std_dev = float(parameters.get('return_std_dev', 0.15))
            num_simulations = int(parameters.get('num_simulations', 1000))

            calculator = MonteCarloCalculator(
                portfolio_value=portfolio_value,
                annual_spending=annual_spending,
                current_age=current_age,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                annual_return_rate=annual_return_rate,
                inflation_rate=inflation_rate,
                return_std_dev=return_std_dev,
                num_simulations=num_simulations,
            )
        elif instance.calculator_type == 'historical':
            # Historical analysis calculator not yet implemented
            result.status = 'failed'
            result.error_message = 'Historical analysis calculator is not yet implemented. Please use the 4% Rule or 4.7% Rule calculators.'
            result.save()
            return
        else:
            result.status = 'failed'
            result.error_message = f'Unsupported calculator type: {instance.calculator_type}'
            result.save()
            return

        # Execute calculation
        calculation_result = calculator.calculate()
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Add defaults used to result data for transparency in UI
        result_with_context = {
            'calculation': calculation_result,
            'defaults_used': defaults_used,
            'parameters_provided': {k: v for k, v in parameters.items() if k in values_used}
        }

        # Save successful result
        result.result_data = result_with_context
        result.status = 'completed'
        result.execution_time_ms = execution_time_ms
        result.error_message = ''
        result.save()

        logger.info(
            f'Calculation completed for scenario {instance.id} ({instance.calculator_type}) '
            f'in {execution_time_ms}ms'
        )

    except Exception as e:
        logger.exception(f'Error running calculation for scenario {instance.id}')
        try:
            result.status = 'failed'
            result.error_message = str(e)
            result.save()
        except Exception as save_error:
            logger.exception(f'Error saving failed result: {save_error}')
