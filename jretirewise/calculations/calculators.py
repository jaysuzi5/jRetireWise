"""
Financial calculation engines for retirement planning.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List
from decimal import Decimal
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class YearProjection:
    """Projection for a single year."""
    year: int
    age: int
    portfolio_value: Decimal
    annual_withdrawal: Decimal
    investment_return: Decimal
    ending_balance: Decimal


class RetirementCalculator:
    """Base class for retirement calculators."""

    def __init__(self, portfolio_value: Decimal, annual_spending: Decimal,
                 current_age: int, retirement_age: int, life_expectancy: int,
                 annual_return_rate: float = 0.07, inflation_rate: float = 0.03):
        """
        Initialize calculator with user parameters.

        Args:
            portfolio_value: Starting portfolio value
            annual_spending: Annual spending needed
            current_age: Current age
            retirement_age: Age to start retirement
            life_expectancy: Expected age of death
            annual_return_rate: Expected annual investment return
            inflation_rate: Expected inflation rate
        """
        # Use Decimal for monetary values to ensure precision
        self.portfolio_value = Decimal(str(portfolio_value))
        self.annual_spending = Decimal(str(annual_spending))
        self.current_age = current_age
        self.retirement_age = retirement_age
        self.life_expectancy = life_expectancy
        self.annual_return_rate = Decimal(str(annual_return_rate))
        self.inflation_rate = Decimal(str(inflation_rate))

    def calculate(self) -> Dict:
        """Calculate and return retirement projection."""
        raise NotImplementedError


class FourPercentCalculator(RetirementCalculator):
    """4% rule calculator - withdraw 4% of initial portfolio."""

    def calculate(self) -> Dict:
        """
        Calculate using 4% rule.

        Returns:
            Dictionary with projection data and success metrics
        """
        projections = []
        current_portfolio = self.portfolio_value

        # Initial 4% withdrawal
        initial_withdrawal = self.portfolio_value * Decimal('0.04')

        years_in_retirement = self.life_expectancy - self.retirement_age

        for year in range(years_in_retirement + 1):
            age = self.retirement_age + year

            if year == 0:
                # First year of retirement
                withdrawal = initial_withdrawal
                portfolio_start = self.portfolio_value
            else:
                # Withdrawal increases with inflation
                withdrawal = initial_withdrawal * ((Decimal(1) + self.inflation_rate) ** year)
                portfolio_start = current_portfolio

            # Investment return
            investment_return = portfolio_start * self.annual_return_rate

            # Ending balance
            ending_balance = portfolio_start + investment_return - withdrawal
            current_portfolio = max(Decimal(0), ending_balance)

            projections.append(YearProjection(
                year=year,
                age=age,
                portfolio_value=portfolio_start,
                annual_withdrawal=withdrawal,
                investment_return=investment_return,
                ending_balance=ending_balance,
            ))

        # Calculate success metrics
        success_rate = self._calculate_success_rate(projections)
        portfolio_depleted_year = self._find_depletion_year(projections)

        return {
            'calculator_type': '4_percent_rule',
            'success_rate': success_rate,
            'portfolio_depleted_year': portfolio_depleted_year,
            'portfolio_depleted_age': self.retirement_age + portfolio_depleted_year if portfolio_depleted_year else None,
            'projections': [self._projection_to_dict(p) for p in projections],
            'final_portfolio_value': float(projections[-1].ending_balance),
            'total_withdrawals': sum(float(p.annual_withdrawal) for p in projections),
        }

    def _calculate_success_rate(self, projections: List[YearProjection]) -> float:
        """Calculate success rate (portfolio never depleted)."""
        for projection in projections:
            if projection.ending_balance < 0:
                return 0.0
        return 100.0

    def _find_depletion_year(self, projections: List[YearProjection]) -> int:
        """Find year when portfolio is depleted."""
        for projection in projections:
            if projection.ending_balance <= 0:
                return projection.year
        return None

    @staticmethod
    def _projection_to_dict(projection: YearProjection) -> Dict:
        """Convert projection to dictionary."""
        return {
            'year': projection.year,
            'age': projection.age,
            'portfolio_value': float(projection.portfolio_value),
            'annual_withdrawal': float(projection.annual_withdrawal),
            'investment_return': float(projection.investment_return),
            'ending_balance': float(projection.ending_balance),
        }


class FourPointSevenPercentCalculator(RetirementCalculator):
    """4.7% rule calculator - slightly more aggressive than 4% rule."""

    def calculate(self) -> Dict:
        """
        Calculate using 4.7% rule.

        Returns:
            Dictionary with projection data and success metrics
        """
        projections = []
        current_portfolio = self.portfolio_value

        # Initial 4.7% withdrawal
        initial_withdrawal = self.portfolio_value * Decimal('0.047')

        years_in_retirement = self.life_expectancy - self.retirement_age

        for year in range(years_in_retirement + 1):
            age = self.retirement_age + year

            if year == 0:
                # First year of retirement
                withdrawal = initial_withdrawal
                portfolio_start = self.portfolio_value
            else:
                # Withdrawal increases with inflation
                withdrawal = initial_withdrawal * ((Decimal(1) + self.inflation_rate) ** year)
                portfolio_start = current_portfolio

            # Investment return
            investment_return = portfolio_start * self.annual_return_rate

            # Ending balance
            ending_balance = portfolio_start + investment_return - withdrawal
            current_portfolio = max(Decimal(0), ending_balance)

            projections.append(YearProjection(
                year=year,
                age=age,
                portfolio_value=portfolio_start,
                annual_withdrawal=withdrawal,
                investment_return=investment_return,
                ending_balance=ending_balance,
            ))

        # Calculate success metrics
        success_rate = self._calculate_success_rate(projections)
        portfolio_depleted_year = self._find_depletion_year(projections)

        return {
            'calculator_type': '4_7_percent_rule',
            'success_rate': success_rate,
            'portfolio_depleted_year': portfolio_depleted_year,
            'portfolio_depleted_age': self.retirement_age + portfolio_depleted_year if portfolio_depleted_year else None,
            'projections': [self._projection_to_dict(p) for p in projections],
            'final_portfolio_value': float(projections[-1].ending_balance),
            'total_withdrawals': sum(float(p.annual_withdrawal) for p in projections),
        }

    def _calculate_success_rate(self, projections: List[YearProjection]) -> float:
        """Calculate success rate (portfolio never depleted)."""
        for projection in projections:
            if projection.ending_balance < 0:
                return 0.0
        return 100.0

    def _find_depletion_year(self, projections: List[YearProjection]) -> int:
        """Find year when portfolio is depleted."""
        for projection in projections:
            if projection.ending_balance <= 0:
                return projection.year
        return None

    @staticmethod
    def _projection_to_dict(projection: YearProjection) -> Dict:
        """Convert projection to dictionary."""
        return {
            'year': projection.year,
            'age': projection.age,
            'portfolio_value': float(projection.portfolio_value),
            'annual_withdrawal': float(projection.annual_withdrawal),
            'investment_return': float(projection.investment_return),
            'ending_balance': float(projection.ending_balance),
        }


class DynamicBucketedWithdrawalCalculator:
    """
    Advanced calculator for dynamic bucketed withdrawal rate scenarios.

    Supports multiple withdrawal buckets (periods) with different rates,
    account constraints, and special considerations (Social Security, pensions, etc.).
    """

    def __init__(self, portfolio_value: Decimal, retirement_age: int,
                 life_expectancy: int, annual_return_rate: float = 0.07,
                 inflation_rate: float = 0.03):
        """Initialize calculator with base parameters."""
        self.portfolio_value = Decimal(str(portfolio_value))
        self.retirement_age = retirement_age
        self.life_expectancy = life_expectancy
        self.annual_return_rate = Decimal(str(annual_return_rate))
        self.inflation_rate = Decimal(str(inflation_rate))

    def calculate(self, buckets: List[Dict]) -> Dict:
        """
        Calculate bucketed withdrawal scenario.

        Args:
            buckets: List of bucket dictionaries with withdrawal rules

        Returns:
            Dictionary with year-by-year projections and summary statistics
        """
        projections = []
        current_portfolio = self.portfolio_value
        years_in_retirement = self.life_expectancy - self.retirement_age

        for year in range(years_in_retirement + 1):
            age = self.retirement_age + year
            bucket = self._find_applicable_bucket(age, year, buckets)

            if not bucket:
                break  # No applicable bucket for this age

            # Calculate withdrawal for this year
            withdrawal_data = self._calculate_year_withdrawal(
                current_portfolio, age, bucket, year
            )

            # Investment return
            portfolio_value_start = current_portfolio
            investment_growth = portfolio_value_start * self.annual_return_rate
            actual_withdrawal = withdrawal_data['actual_withdrawal']

            # Ending balance
            ending_balance = portfolio_value_start + investment_growth - actual_withdrawal
            ending_balance = max(Decimal(0), ending_balance)

            # Build projection record
            projection = {
                'year': year,
                'age': age,
                'bucket_name': bucket.get('bucket_name', 'Unknown'),
                'target_rate': bucket.get('target_withdrawal_rate', 0),
                'calculated_withdrawal': float(withdrawal_data['calculated_withdrawal']),
                'actual_withdrawal': float(actual_withdrawal),
                'portfolio_value_start': float(portfolio_value_start),
                'investment_growth': float(investment_growth),
                'portfolio_value_end': float(ending_balance),
                'pension_income': float(withdrawal_data.get('pension_income', 0)),
                'social_security_income': float(withdrawal_data.get('social_security_income', 0)),
                'total_available_income': float(
                    actual_withdrawal +
                    withdrawal_data.get('pension_income', 0) +
                    withdrawal_data.get('social_security_income', 0)
                ),
                'notes': withdrawal_data.get('notes', ''),
                'flags': withdrawal_data.get('flags', []),
            }

            projections.append(projection)
            current_portfolio = ending_balance

            # Stop if portfolio depleted
            if ending_balance <= 0:
                break

        # Calculate summary statistics
        summary = self._calculate_summary(projections)

        return {
            'calculator_type': 'bucketed_withdrawal',
            'projections': projections,
            'summary': summary,
        }

    def _find_applicable_bucket(self, age: int, year: int, buckets: List[Dict]) -> Dict:
        """Find the bucket that applies for the given age/year."""
        for bucket in buckets:
            # Check age range
            start_age = bucket.get('start_age')
            end_age = bucket.get('end_age')

            if start_age and end_age:
                if start_age <= age <= end_age:
                    return bucket
            elif start_age and age >= start_age:
                return bucket

        return None

    def _calculate_year_withdrawal(self, portfolio_value: Decimal, age: int,
                                   bucket: Dict, year: int) -> Dict:
        """Calculate withdrawal amount for a specific year."""
        # Check for manual override
        if bucket.get('manual_withdrawal_override'):
            return {
                'calculated_withdrawal': Decimal(str(bucket['manual_withdrawal_override'])),
                'actual_withdrawal': Decimal(str(bucket['manual_withdrawal_override'])),
                'pension_income': Decimal(str(bucket.get('expected_pension_income', 0))),
                'social_security_income': Decimal(str(bucket.get('expected_social_security_income', 0))),
                'notes': 'Manual override applied',
                'flags': [],
            }

        # Calculate based on withdrawal rate
        withdrawal_rate = Decimal(str(bucket.get('target_withdrawal_rate', 4.0))) / Decimal(100)
        calculated_withdrawal = portfolio_value * withdrawal_rate

        # Apply min/max constraints
        min_amount = bucket.get('min_withdrawal_amount')
        max_amount = bucket.get('max_withdrawal_amount')

        if min_amount:
            calculated_withdrawal = max(calculated_withdrawal, Decimal(str(min_amount)))
        if max_amount:
            calculated_withdrawal = min(calculated_withdrawal, Decimal(str(max_amount)))

        # Apply special adjustments
        pension_income = Decimal(str(bucket.get('expected_pension_income', 0)))
        ss_income = Decimal(str(bucket.get('expected_social_security_income', 0)))
        healthcare_adjustment = Decimal(str(bucket.get('healthcare_cost_adjustment', 0)))

        # Adjust for other income sources
        actual_withdrawal = max(Decimal(0), calculated_withdrawal + healthcare_adjustment - pension_income - ss_income)

        flags = []
        notes = []

        # Check for early access penalties (before 59.5)
        if age < 59 and bucket.get('allowed_account_types'):
            flags.append('early_access_penalty_risk')
            notes.append('Early access may incur penalties')

        # Tax considerations
        if bucket.get('tax_loss_harvesting_enabled'):
            flags.append('tax_loss_harvesting')
            notes.append('Tax-loss harvesting opportunity')

        if bucket.get('roth_conversion_enabled'):
            flags.append('roth_conversion')
            notes.append('Roth conversion opportunity')

        return {
            'calculated_withdrawal': calculated_withdrawal,
            'actual_withdrawal': actual_withdrawal,
            'pension_income': pension_income,
            'social_security_income': ss_income,
            'notes': '; '.join(notes) if notes else '',
            'flags': flags,
        }

    @staticmethod
    def _calculate_summary(projections: List[Dict]) -> Dict:
        """Calculate summary statistics from projections."""
        if not projections:
            return {}

        total_withdrawal = sum(Decimal(str(p['actual_withdrawal'])) for p in projections)
        final_value = projections[-1]['portfolio_value_end']
        depleted = final_value <= 0

        # Find milestone values
        milestones = {}
        for p in projections:
            if p['age'] in [65, 70, 75, 80, 85, 90]:
                milestones[f"age_{p['age']}"] = p['portfolio_value_end']

        return {
            'total_projections': len(projections),
            'final_portfolio_value': final_value,
            'portfolio_depleted': depleted,
            'total_withdrawals': float(total_withdrawal),
            'average_annual_withdrawal': float(total_withdrawal / len(projections)) if projections else 0,
            'milestones': milestones,
            'success_rate': 100.0 if not depleted else 0.0,
        }
