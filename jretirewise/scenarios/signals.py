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
        user_profile = instance.user.profile

        # Use scenario parameters or fall back to user's financial profile
        portfolio_value = float(parameters.get('portfolio_value', user_profile.current_portfolio_value))
        annual_spending = float(parameters.get('annual_spending', user_profile.annual_spending))
        current_age = int(parameters.get('current_age', user_profile.current_age))
        retirement_age = int(parameters.get('retirement_age', user_profile.retirement_age))
        life_expectancy = int(parameters.get('life_expectancy', user_profile.life_expectancy))

        # Optional parameters with defaults
        annual_return_rate = float(parameters.get('annual_return_rate', 0.07))
        inflation_rate = float(parameters.get('inflation_rate', 0.03))

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

        # Save successful result
        result.result_data = calculation_result
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
