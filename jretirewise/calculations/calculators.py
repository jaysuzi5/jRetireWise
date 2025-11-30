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
        self.portfolio_value = float(portfolio_value)
        self.annual_spending = float(annual_spending)
        self.current_age = current_age
        self.retirement_age = retirement_age
        self.life_expectancy = life_expectancy
        self.annual_return_rate = annual_return_rate
        self.inflation_rate = inflation_rate

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
        initial_withdrawal = self.portfolio_value * 0.04

        years_in_retirement = self.life_expectancy - self.retirement_age

        for year in range(years_in_retirement + 1):
            age = self.retirement_age + year

            if year == 0:
                # First year of retirement
                withdrawal = initial_withdrawal
                portfolio_start = self.portfolio_value
            else:
                # Withdrawal increases with inflation
                withdrawal = initial_withdrawal * ((1 + self.inflation_rate) ** year)
                portfolio_start = current_portfolio

            # Investment return
            investment_return = portfolio_start * self.annual_return_rate

            # Ending balance
            ending_balance = portfolio_start + investment_return - withdrawal
            current_portfolio = max(0, ending_balance)

            projections.append(YearProjection(
                year=year,
                age=age,
                portfolio_value=Decimal(str(portfolio_start)),
                annual_withdrawal=Decimal(str(withdrawal)),
                investment_return=Decimal(str(investment_return)),
                ending_balance=Decimal(str(ending_balance)),
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
        initial_withdrawal = self.portfolio_value * 0.047

        years_in_retirement = self.life_expectancy - self.retirement_age

        for year in range(years_in_retirement + 1):
            age = self.retirement_age + year

            if year == 0:
                # First year of retirement
                withdrawal = initial_withdrawal
                portfolio_start = self.portfolio_value
            else:
                # Withdrawal increases with inflation
                withdrawal = initial_withdrawal * ((1 + self.inflation_rate) ** year)
                portfolio_start = current_portfolio

            # Investment return
            investment_return = portfolio_start * self.annual_return_rate

            # Ending balance
            ending_balance = portfolio_start + investment_return - withdrawal
            current_portfolio = max(0, ending_balance)

            projections.append(YearProjection(
                year=year,
                age=age,
                portfolio_value=Decimal(str(portfolio_start)),
                annual_withdrawal=Decimal(str(withdrawal)),
                investment_return=Decimal(str(investment_return)),
                ending_balance=Decimal(str(ending_balance)),
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
