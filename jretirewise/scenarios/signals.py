"""
Signal handlers for scenario calculations.
"""

import time
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import RetirementScenario, CalculationResult
from jretirewise.calculations.calculators import FourPercentCalculator, FourPointSevenPercentCalculator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=RetirementScenario)
def run_scenario_calculation(sender, instance, created, **kwargs):
    """
    Automatically run calculation when a scenario is created or calculator_type changes.
    """
    # Only run for new scenarios
    if not created:
        return

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

        # Use scenario parameters or fall back to user's financial profile
        portfolio_value = float(parameters.get('portfolio_value', financial_profile.current_portfolio_value))
        annual_spending = float(parameters.get('annual_spending', financial_profile.annual_spending))
        current_age = int(parameters.get('current_age', financial_profile.current_age))
        retirement_age = int(parameters.get('retirement_age', financial_profile.retirement_age))
        life_expectancy = int(parameters.get('life_expectancy', financial_profile.life_expectancy))

        # Optional parameters with defaults
        # Accept both 'annual_return' and 'annual_return_rate' for flexibility
        annual_return_rate = float(parameters.get('annual_return_rate') or parameters.get('annual_return', 0.07))
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

        # Create a defaults dict showing actual values used
        defaults_used = {
            'portfolio_value': portfolio_value if not values_used['portfolio_value'] else None,
            'annual_spending': annual_spending if not values_used['annual_spending'] else None,
            'current_age': current_age if not values_used['current_age'] else None,
            'retirement_age': retirement_age if not values_used['retirement_age'] else None,
            'life_expectancy': life_expectancy if not values_used['life_expectancy'] else None,
            'annual_return_rate': annual_return_rate if not values_used['annual_return_rate'] else None,
            'inflation_rate': inflation_rate if not values_used['inflation_rate'] else None,
        }

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
