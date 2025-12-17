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
        # Ensure ages are integers for range() operations
        self.current_age = int(current_age)
        self.retirement_age = int(retirement_age)
        self.life_expectancy = int(life_expectancy)
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


class MonteCarloCalculator(RetirementCalculator):
    """
    Monte Carlo simulation calculator for retirement planning.

    Runs thousands of simulations with randomized market returns to estimate
    the probability of portfolio success over the retirement period.
    """

    def __init__(self, portfolio_value, annual_spending,
                 current_age: int, retirement_age: int, life_expectancy: int,
                 annual_return_rate: float = 0.07, inflation_rate: float = 0.03,
                 return_std_dev: float = 0.15, num_simulations: int = 1000):
        """
        Initialize Monte Carlo calculator.

        Args:
            portfolio_value: Starting portfolio value
            annual_spending: Annual spending needed
            current_age: Current age
            retirement_age: Age to start retirement
            life_expectancy: Expected age of death
            annual_return_rate: Expected average annual return (mean)
            inflation_rate: Expected inflation rate
            return_std_dev: Standard deviation of returns (volatility)
            num_simulations: Number of Monte Carlo simulations to run
        """
        super().__init__(portfolio_value, annual_spending, current_age,
                         retirement_age, life_expectancy, annual_return_rate,
                         inflation_rate)
        self.return_std_dev = float(return_std_dev)
        self.num_simulations = int(num_simulations)

    def calculate(self) -> Dict:
        """
        Run Monte Carlo simulation.

        Returns:
            Dictionary with simulation results, percentiles, and success metrics
        """
        years_in_retirement = self.life_expectancy - self.retirement_age

        # Use numpy for efficient simulation
        mean_return = float(self.annual_return_rate)
        inflation = float(self.inflation_rate)
        initial_withdrawal = float(self.portfolio_value) * 0.04  # 4% initial withdrawal

        # Run all simulations
        all_simulations = []
        successful_simulations = 0

        for sim in range(self.num_simulations):
            portfolio = float(self.portfolio_value)
            withdrawal = initial_withdrawal
            yearly_values = [portfolio]
            depleted_year = None

            for year in range(1, years_in_retirement + 1):
                # Random return from normal distribution
                annual_return = np.random.normal(mean_return, self.return_std_dev)

                # Apply return
                portfolio = portfolio * (1 + annual_return)

                # Adjust withdrawal for inflation
                withdrawal = withdrawal * (1 + inflation)

                # Make withdrawal
                portfolio = portfolio - withdrawal

                # Track if depleted
                if portfolio <= 0:
                    portfolio = 0
                    if depleted_year is None:
                        depleted_year = year

                yearly_values.append(portfolio)

            # Track success (portfolio never depleted)
            if depleted_year is None:
                successful_simulations += 1

            all_simulations.append({
                'yearly_values': yearly_values,
                'final_value': portfolio,
                'depleted_year': depleted_year,
                'success': depleted_year is None
            })

        # Calculate success rate
        success_rate = (successful_simulations / self.num_simulations) * 100

        # Calculate percentiles for final portfolio values
        final_values = [sim['final_value'] for sim in all_simulations]
        percentiles = {
            'p5': float(np.percentile(final_values, 5)),
            'p10': float(np.percentile(final_values, 10)),
            'p25': float(np.percentile(final_values, 25)),
            'p50': float(np.percentile(final_values, 50)),  # Median
            'p75': float(np.percentile(final_values, 75)),
            'p90': float(np.percentile(final_values, 90)),
            'p95': float(np.percentile(final_values, 95)),
        }

        # Calculate year-by-year percentile projections for charting
        yearly_percentiles = []
        for year in range(years_in_retirement + 1):
            year_values = [sim['yearly_values'][year] for sim in all_simulations]
            yearly_percentiles.append({
                'year': year,
                'age': self.retirement_age + year,
                'p5': float(np.percentile(year_values, 5)),
                'p10': float(np.percentile(year_values, 10)),
                'p25': float(np.percentile(year_values, 25)),
                'p50': float(np.percentile(year_values, 50)),
                'p75': float(np.percentile(year_values, 75)),
                'p90': float(np.percentile(year_values, 90)),
                'p95': float(np.percentile(year_values, 95)),
                'mean': float(np.mean(year_values)),
            })

        # Find depletion statistics
        depleted_sims = [sim for sim in all_simulations if sim['depleted_year'] is not None]
        depletion_stats = None
        if depleted_sims:
            depletion_years = [sim['depleted_year'] for sim in depleted_sims]
            depletion_stats = {
                'count': len(depleted_sims),
                'earliest_year': min(depletion_years),
                'latest_year': max(depletion_years),
                'median_year': float(np.median(depletion_years)),
                'earliest_age': self.retirement_age + min(depletion_years),
                'median_age': self.retirement_age + int(np.median(depletion_years)),
            }

        return {
            'calculator_type': 'monte_carlo',
            'num_simulations': self.num_simulations,
            'success_rate': success_rate,
            'failure_rate': 100 - success_rate,
            'successful_simulations': successful_simulations,
            'failed_simulations': self.num_simulations - successful_simulations,
            'final_value_percentiles': percentiles,
            'yearly_percentiles': yearly_percentiles,
            'depletion_stats': depletion_stats,
            'parameters': {
                'mean_return': mean_return * 100,  # Convert to percentage for display
                'return_std_dev': self.return_std_dev * 100,
                'inflation_rate': inflation * 100,
                'initial_withdrawal_rate': 4.0,
                'years_in_retirement': years_in_retirement,
            },
            'summary': {
                'median_final_value': percentiles['p50'],
                'worst_case_final_value': percentiles['p5'],
                'best_case_final_value': percentiles['p95'],
            }
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
        # Ensure ages are integers for range() operations
        self.retirement_age = int(retirement_age)
        self.life_expectancy = int(life_expectancy)
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


class EnhancedMonteCarloCalculator:
    """
    Enhanced Monte Carlo simulation with dual calculation modes.

    Mode 1: find_withdrawal - Binary search to find safe withdrawal for target success rate
    Mode 2: evaluate_success - Evaluate success rate for fixed withdrawal amount

    Supports Social Security integration to reduce portfolio withdrawal needs.
    """

    def __init__(
        self,
        portfolio_value,
        retirement_age: int,
        life_expectancy: int,
        annual_return_rate: float = 0.07,
        inflation_rate: float = 0.03,
        return_std_dev: float = 0.15,
        num_simulations: int = 1000,
        # Mode selection
        mode: str = 'evaluate_success',  # 'find_withdrawal' or 'evaluate_success'
        # For evaluate_success mode
        withdrawal_amount: float = None,  # Annual withdrawal amount
        withdrawal_rate: float = None,    # Alternative: withdrawal as rate (e.g., 0.04)
        # For find_withdrawal mode
        target_success_rate: float = 90.0,  # Target success percentage
        # Social Security parameters
        social_security_start_age: int = None,
        social_security_monthly_benefit: float = 0,
        # Pension parameters
        pension_annual: float = 0,
        # Time step configuration
        periods_per_year: int = 12,  # 12 for monthly, 1 for annual
    ):
        """
        Initialize Enhanced Monte Carlo calculator.

        Args:
            portfolio_value: Starting portfolio value
            retirement_age: Age when retirement begins
            life_expectancy: Expected age of death
            annual_return_rate: Expected average annual return (decimal, e.g., 0.07)
            inflation_rate: Expected inflation rate (decimal, e.g., 0.03)
            return_std_dev: Standard deviation of returns (volatility)
            num_simulations: Number of Monte Carlo simulations to run
            mode: 'find_withdrawal' or 'evaluate_success'
            withdrawal_amount: For evaluate_success mode - annual withdrawal
            withdrawal_rate: For evaluate_success mode - withdrawal as rate
            target_success_rate: For find_withdrawal mode - target success percentage
            social_security_start_age: Age when SS benefits begin (62-70)
            social_security_monthly_benefit: Monthly SS benefit amount
            pension_annual: Annual pension income
            periods_per_year: Time steps per year (12 for monthly, 1 for annual)
        """
        self.portfolio_value = float(portfolio_value)
        self.retirement_age = int(retirement_age)
        self.life_expectancy = int(life_expectancy)
        self.annual_return_rate = float(annual_return_rate)
        self.inflation_rate = float(inflation_rate)
        self.return_std_dev = float(return_std_dev)
        self.num_simulations = int(num_simulations)
        self.mode = mode
        self.withdrawal_amount = float(withdrawal_amount) if withdrawal_amount else None
        self.withdrawal_rate = float(withdrawal_rate) if withdrawal_rate else None
        self.target_success_rate = float(target_success_rate)
        self.social_security_start_age = int(social_security_start_age) if social_security_start_age else None
        self.social_security_monthly_benefit = float(social_security_monthly_benefit)
        self.pension_annual = float(pension_annual)
        self.periods_per_year = int(periods_per_year)

        # Pre-calculate time step size
        self.dt = 1.0 / self.periods_per_year

    def calculate(self) -> Dict:
        """
        Main calculation entry point.

        Returns:
            Dictionary with simulation results based on mode
        """
        if self.mode == 'find_withdrawal':
            return self._find_safe_withdrawal()
        else:
            return self._evaluate_success()

    def _find_safe_withdrawal(self) -> Dict:
        """
        Binary search to find withdrawal amount achieving target success rate.

        Algorithm:
        1. Start with bounds: low = 0, high = portfolio_value * 0.15 (15%)
        2. Binary search: mid = (low + high) / 2
        3. Run simulation with mid as withdrawal
        4. If success_rate > target: increase low (can withdraw more)
        5. If success_rate < target: decrease high (must withdraw less)
        6. Converge when |success_rate - target| < tolerance
        """
        tolerance = 0.5  # Accept within 0.5% of target
        max_iterations = 25

        low = 0
        high = self.portfolio_value * 0.15  # Max 15% initial withdrawal rate

        best_withdrawal = 0
        best_result = None

        for iteration in range(max_iterations):
            mid = (low + high) / 2
            result = self._run_simulation(annual_withdrawal=mid)

            # Track the best result closest to target
            if best_result is None or abs(result['success_rate'] - self.target_success_rate) < abs(best_result['success_rate'] - self.target_success_rate):
                best_withdrawal = mid
                best_result = result

            if abs(result['success_rate'] - self.target_success_rate) < tolerance:
                break
            elif result['success_rate'] > self.target_success_rate:
                low = mid  # Can afford more withdrawal
            else:
                high = mid  # Need to withdraw less

        # Get final result with the found withdrawal
        final_result = self._run_simulation(annual_withdrawal=best_withdrawal)

        # Calculate 4% rule comparison
        four_percent_withdrawal = self.portfolio_value * 0.04
        four_percent_result = self._run_simulation(annual_withdrawal=four_percent_withdrawal)

        # Calculate constant return trajectory for charting
        constant_return_trajectory = self._calculate_constant_return_trajectory(best_withdrawal)

        return {
            'calculator_type': 'monte_carlo',
            'mode': 'find_withdrawal',
            'target_success_rate': self.target_success_rate,
            'achieved_success_rate': final_result['success_rate'],
            'safe_withdrawal_annual': best_withdrawal,
            'safe_withdrawal_monthly': best_withdrawal / 12,
            'safe_withdrawal_rate': (best_withdrawal / self.portfolio_value) * 100,
            'four_percent_comparison': {
                'withdrawal_annual': four_percent_withdrawal,
                'withdrawal_monthly': four_percent_withdrawal / 12,
                'success_rate': four_percent_result['success_rate'],
                'difference_amount': best_withdrawal - four_percent_withdrawal,
                'difference_percent': ((best_withdrawal - four_percent_withdrawal) / four_percent_withdrawal) * 100 if four_percent_withdrawal > 0 else 0,
            },
            'constant_return_trajectory': constant_return_trajectory,
            **final_result,
        }

    def _evaluate_success(self) -> Dict:
        """
        Evaluate success rate for given withdrawal amount.

        Returns:
            Dictionary with success rate and detailed statistics
        """
        # Determine withdrawal amount
        if self.withdrawal_amount:
            annual_withdrawal = self.withdrawal_amount
        elif self.withdrawal_rate:
            annual_withdrawal = self.portfolio_value * self.withdrawal_rate
        else:
            annual_withdrawal = self.portfolio_value * 0.04  # Default 4%

        result = self._run_simulation(annual_withdrawal=annual_withdrawal)

        # 4% comparison
        four_percent_withdrawal = self.portfolio_value * 0.04
        four_percent_result = self._run_simulation(annual_withdrawal=four_percent_withdrawal)

        # Calculate constant return trajectory for charting
        constant_return_trajectory = self._calculate_constant_return_trajectory(annual_withdrawal)

        return {
            'calculator_type': 'monte_carlo',
            'mode': 'evaluate_success',
            'withdrawal_annual': annual_withdrawal,
            'withdrawal_monthly': annual_withdrawal / 12,
            'withdrawal_rate': (annual_withdrawal / self.portfolio_value) * 100,
            'four_percent_comparison': {
                'withdrawal_annual': four_percent_withdrawal,
                'withdrawal_monthly': four_percent_withdrawal / 12,
                'success_rate': four_percent_result['success_rate'],
            },
            'constant_return_trajectory': constant_return_trajectory,
            **result,
        }

    def _gbm_step(self, portfolio: float) -> float:
        """
        Apply one time step of Geometric Brownian Motion.

        Uses the formula: P * exp((μ - 0.5σ²)dt + σ√dt·Z)
        where Z is a standard normal random variable.

        This properly models lognormal returns and prevents impossible
        negative portfolio values from returns alone.

        Args:
            portfolio: Current portfolio value

        Returns:
            New portfolio value after applying GBM return
        """
        Z = np.random.standard_normal()
        drift = (self.annual_return_rate - 0.5 * self.return_std_dev ** 2) * self.dt
        diffusion = self.return_std_dev * np.sqrt(self.dt) * Z
        return portfolio * np.exp(drift + diffusion)

    def _run_simulation(self, annual_withdrawal: float) -> Dict:
        """
        Run Monte Carlo simulation using Geometric Brownian Motion.

        Supports monthly or annual time steps. Social Security reduces
        portfolio withdrawal needs once the beneficiary reaches
        social_security_start_age.

        Args:
            annual_withdrawal: Initial annual withdrawal amount (before SS)

        Returns:
            Dictionary with simulation statistics and percentiles
        """
        years_in_retirement = self.life_expectancy - self.retirement_age
        total_periods = years_in_retirement * self.periods_per_year
        all_simulations = []
        successful_simulations = 0

        # Convert withdrawals and income to per-period amounts
        ss_annual = self.social_security_monthly_benefit * 12
        period_withdrawal_base = annual_withdrawal / self.periods_per_year
        ss_period = ss_annual / self.periods_per_year
        pension_period = self.pension_annual / self.periods_per_year

        # SS start age (default to 65 if not specified)
        ss_start = self.social_security_start_age if self.social_security_start_age else 65

        for sim in range(self.num_simulations):
            portfolio = self.portfolio_value
            yearly_values = [portfolio]
            depleted_year = None

            for period in range(1, total_periods + 1):
                # Calculate current time in years
                t = period * self.dt
                current_age = self.retirement_age + t

                # Apply GBM return for this period
                portfolio = self._gbm_step(portfolio)

                # Calculate inflation-adjusted withdrawal for this period
                # Withdrawal grows with inflation from start
                inflation_factor = (1 + self.inflation_rate) ** t
                period_withdrawal = period_withdrawal_base * inflation_factor

                # Calculate net withdrawal (subtract SS and pension if eligible)
                net_withdrawal = period_withdrawal

                # Social Security kicks in at start age
                if ss_period > 0 and current_age >= ss_start:
                    # SS also increases with inflation (simplified COLA)
                    # Inflation adjustment from SS start, not retirement start
                    years_since_ss_start = current_age - ss_start
                    ss_inflation_factor = (1 + self.inflation_rate) ** years_since_ss_start
                    ss_adjusted = ss_period * ss_inflation_factor
                    net_withdrawal = max(0, net_withdrawal - ss_adjusted)

                # Subtract pension if applicable (also inflation adjusted from start)
                if pension_period > 0:
                    pension_adjusted = pension_period * inflation_factor
                    net_withdrawal = max(0, net_withdrawal - pension_adjusted)

                # Make withdrawal
                portfolio = portfolio - net_withdrawal

                if portfolio <= 0:
                    portfolio = 0
                    if depleted_year is None:
                        depleted_year = int(np.ceil(t))

                # Record yearly values (at end of each year)
                if period % self.periods_per_year == 0:
                    yearly_values.append(portfolio)

            if depleted_year is None:
                successful_simulations += 1

            all_simulations.append({
                'yearly_values': yearly_values,
                'final_value': portfolio,
                'depleted_year': depleted_year,
            })

        # Calculate statistics
        success_rate = (successful_simulations / self.num_simulations) * 100

        # Final value percentiles
        final_values = [sim['final_value'] for sim in all_simulations]
        final_percentiles = {
            'p5': float(np.percentile(final_values, 5)),
            'p10': float(np.percentile(final_values, 10)),
            'p25': float(np.percentile(final_values, 25)),
            'p50': float(np.percentile(final_values, 50)),
            'p75': float(np.percentile(final_values, 75)),
            'p90': float(np.percentile(final_values, 90)),
            'p95': float(np.percentile(final_values, 95)),
        }

        # Yearly percentiles for charting
        yearly_percentiles = []
        for year in range(years_in_retirement + 1):
            year_values = [sim['yearly_values'][year] for sim in all_simulations]
            yearly_percentiles.append({
                'year': year,
                'age': self.retirement_age + year,
                'p5': float(np.percentile(year_values, 5)),
                'p10': float(np.percentile(year_values, 10)),
                'p25': float(np.percentile(year_values, 25)),
                'p50': float(np.percentile(year_values, 50)),
                'p75': float(np.percentile(year_values, 75)),
                'p90': float(np.percentile(year_values, 90)),
                'p95': float(np.percentile(year_values, 95)),
                'mean': float(np.mean(year_values)),
            })

        # Depletion statistics
        depletion_stats = None
        depleted_sims = [s for s in all_simulations if s['depleted_year'] is not None]
        if depleted_sims:
            depletion_years = [s['depleted_year'] for s in depleted_sims]
            depletion_stats = {
                'count': len(depleted_sims),
                'earliest_year': min(depletion_years),
                'latest_year': max(depletion_years),
                'median_year': float(np.median(depletion_years)),
                'earliest_age': self.retirement_age + min(depletion_years),
                'median_age': self.retirement_age + int(np.median(depletion_years)),
            }

        return {
            'success_rate': success_rate,
            'failure_rate': 100 - success_rate,
            'num_simulations': self.num_simulations,
            'successful_simulations': successful_simulations,
            'failed_simulations': self.num_simulations - successful_simulations,
            'final_value_percentiles': final_percentiles,
            'yearly_percentiles': yearly_percentiles,
            'depletion_stats': depletion_stats,
            'parameters': {
                'portfolio_value': self.portfolio_value,
                'retirement_age': self.retirement_age,
                'life_expectancy': self.life_expectancy,
                'mean_return': self.annual_return_rate * 100,
                'return_std_dev': self.return_std_dev * 100,
                'inflation_rate': self.inflation_rate * 100,
                'years_in_retirement': years_in_retirement,
                'num_simulations': self.num_simulations,
                'periods_per_year': self.periods_per_year,
                'social_security_start_age': self.social_security_start_age if self.social_security_start_age else 65,
                'social_security_annual': ss_annual,
                'pension_annual': self.pension_annual,
            },
            'summary': {
                'median_final_value': final_percentiles['p50'],
                'worst_case_final_value': final_percentiles['p5'],
                'best_case_final_value': final_percentiles['p95'],
            },
        }

    def _calculate_constant_return_trajectory(self, annual_withdrawal: float) -> List[Dict]:
        """
        Calculate deterministic trajectory assuming constant returns (no volatility).

        This provides a comparison baseline showing what would happen with
        average returns and no market volatility. Uses the same time step
        granularity as the Monte Carlo simulation.

        Args:
            annual_withdrawal: Initial annual withdrawal amount

        Returns:
            List of year-by-year portfolio values with constant return
        """
        years_in_retirement = self.life_expectancy - self.retirement_age
        total_periods = years_in_retirement * self.periods_per_year
        trajectory = []
        portfolio = self.portfolio_value

        # Convert to per-period amounts
        ss_annual = self.social_security_monthly_benefit * 12
        period_withdrawal_base = annual_withdrawal / self.periods_per_year
        ss_period = ss_annual / self.periods_per_year
        pension_period = self.pension_annual / self.periods_per_year

        # SS start age (default to 65 if not specified)
        ss_start = self.social_security_start_age if self.social_security_start_age else 65

        # Constant return per period (using GBM drift without randomness)
        # For constant return, we use the expected return directly
        period_return = (1 + self.annual_return_rate) ** self.dt - 1

        # Record initial value
        trajectory.append({
            'year': 0,
            'age': self.retirement_age,
            'portfolio_value': portfolio,
        })

        for period in range(1, total_periods + 1):
            # Calculate current time in years
            t = period * self.dt
            current_age = self.retirement_age + t

            # Apply constant return for this period
            portfolio = portfolio * (1 + period_return)

            # Calculate inflation-adjusted withdrawal for this period
            inflation_factor = (1 + self.inflation_rate) ** t
            period_withdrawal = period_withdrawal_base * inflation_factor

            # Calculate net withdrawal
            net_withdrawal = period_withdrawal

            # Social Security kicks in at start age
            if ss_period > 0 and current_age >= ss_start:
                years_since_ss_start = current_age - ss_start
                ss_inflation_factor = (1 + self.inflation_rate) ** years_since_ss_start
                ss_adjusted = ss_period * ss_inflation_factor
                net_withdrawal = max(0, net_withdrawal - ss_adjusted)

            # Pension (inflation adjusted from start)
            if pension_period > 0:
                pension_adjusted = pension_period * inflation_factor
                net_withdrawal = max(0, net_withdrawal - pension_adjusted)

            portfolio = max(0, portfolio - net_withdrawal)

            # Record yearly values (at end of each year)
            if period % self.periods_per_year == 0:
                year = period // self.periods_per_year
                trajectory.append({
                    'year': year,
                    'age': self.retirement_age + year,
                    'portfolio_value': portfolio,
                })

        return trajectory


class HistoricalPeriodCalculator:
    """
    Historical Period Analysis Calculator.

    Tests retirement scenarios against actual historical market returns
    from 1960 to present. Identifies:
    - Success rate across all historical periods
    - Best/worst case scenarios
    - Vulnerable periods where the portfolio would fail
    - Sequence of returns risk analysis
    """

    def __init__(
        self,
        portfolio_value: float,
        retirement_age: int,
        life_expectancy: int,
        withdrawal_rate: float = 0.04,
        withdrawal_amount: float = None,
        stock_allocation: float = 0.60,
        social_security_start_age: int = None,
        social_security_annual: float = 0,
        pension_annual: float = 0,
    ):
        """
        Initialize Historical Period Calculator.

        Args:
            portfolio_value: Starting portfolio value
            retirement_age: Age when retirement begins
            life_expectancy: Expected age of death
            withdrawal_rate: Annual withdrawal rate (e.g., 0.04 for 4%)
            withdrawal_amount: Fixed withdrawal amount (overrides rate if set)
            stock_allocation: Percentage of portfolio in stocks (0.0-1.0)
            social_security_start_age: Age when SS benefits begin
            social_security_annual: Annual SS benefit amount
            pension_annual: Annual pension income
        """
        self.portfolio_value = float(portfolio_value)
        self.retirement_age = int(retirement_age)
        self.life_expectancy = int(life_expectancy)
        self.withdrawal_rate = float(withdrawal_rate)
        self.withdrawal_amount = float(withdrawal_amount) if withdrawal_amount else None
        self.stock_allocation = float(stock_allocation)
        self.social_security_start_age = int(social_security_start_age) if social_security_start_age else None
        self.social_security_annual = float(social_security_annual)
        self.pension_annual = float(pension_annual)

        self.years_in_retirement = self.life_expectancy - self.retirement_age

    def calculate(self) -> Dict:
        """
        Run historical period analysis across all available starting years.

        Returns:
            Dictionary with success rate, period results, best/worst cases
        """
        from .data import (
            get_returns_for_period,
            get_inflation_for_period,
            get_available_start_years,
            NOTABLE_PERIODS,
        )

        # Get all valid starting years
        available_years = get_available_start_years(self.years_in_retirement)

        if not available_years:
            return {
                'calculator_type': 'historical',
                'error': 'No historical data available for the requested retirement period',
                'success_rate': 0,
            }

        # Run simulation for each starting year
        period_results = []
        successful_periods = 0
        failed_periods = []

        for start_year in available_years:
            result = self._simulate_period(
                start_year,
                get_returns_for_period(start_year, self.years_in_retirement, self.stock_allocation),
                get_inflation_for_period(start_year, self.years_in_retirement),
            )
            period_results.append(result)

            if result['success']:
                successful_periods += 1
            else:
                failed_periods.append(result)

        # Calculate success rate
        success_rate = (successful_periods / len(available_years)) * 100

        # Find best and worst cases
        sorted_by_final = sorted(period_results, key=lambda x: x['final_portfolio_value'])
        worst_case = sorted_by_final[0]
        best_case = sorted_by_final[-1]

        # Find median case
        median_idx = len(sorted_by_final) // 2
        median_case = sorted_by_final[median_idx]

        # Analyze vulnerable periods (where failure occurred)
        vulnerable_periods = self._analyze_vulnerable_periods(failed_periods)

        # Test notable historical periods
        notable_results = self._test_notable_periods(NOTABLE_PERIODS)

        # Calculate percentiles for final portfolio values
        final_values = [r['final_portfolio_value'] for r in period_results]
        percentiles = {
            'p5': float(np.percentile(final_values, 5)),
            'p10': float(np.percentile(final_values, 10)),
            'p25': float(np.percentile(final_values, 25)),
            'p50': float(np.percentile(final_values, 50)),
            'p75': float(np.percentile(final_values, 75)),
            'p90': float(np.percentile(final_values, 90)),
            'p95': float(np.percentile(final_values, 95)),
        }

        # Build yearly percentile data for charting
        yearly_percentiles = self._calculate_yearly_percentiles(period_results)

        return {
            'calculator_type': 'historical',
            'success_rate': success_rate,
            'total_periods_tested': len(available_years),
            'successful_periods': successful_periods,
            'failed_periods': len(failed_periods),
            'years_tested': f"{min(available_years)}-{max(available_years)}",
            'years_in_retirement': self.years_in_retirement,
            'best_case': {
                'start_year': best_case['start_year'],
                'final_portfolio_value': best_case['final_portfolio_value'],
                'total_withdrawals': best_case['total_withdrawals'],
                'average_return': best_case['average_return'],
            },
            'worst_case': {
                'start_year': worst_case['start_year'],
                'final_portfolio_value': worst_case['final_portfolio_value'],
                'total_withdrawals': worst_case['total_withdrawals'],
                'years_lasted': worst_case['years_lasted'],
                'average_return': worst_case['average_return'],
            },
            'median_case': {
                'start_year': median_case['start_year'],
                'final_portfolio_value': median_case['final_portfolio_value'],
                'total_withdrawals': median_case['total_withdrawals'],
                'average_return': median_case['average_return'],
            },
            'final_value_percentiles': percentiles,
            'yearly_percentiles': yearly_percentiles,
            'vulnerable_periods': vulnerable_periods,
            'notable_periods': notable_results,
            'period_results': period_results,
            'parameters': {
                'portfolio_value': self.portfolio_value,
                'retirement_age': self.retirement_age,
                'life_expectancy': self.life_expectancy,
                'withdrawal_rate': self.withdrawal_rate * 100,
                'stock_allocation': self.stock_allocation * 100,
                'social_security_start_age': self.social_security_start_age,
                'social_security_annual': self.social_security_annual,
                'pension_annual': self.pension_annual,
            },
        }

    def _simulate_period(self, start_year: int, returns: List[float],
                         inflation_rates: List[float]) -> Dict:
        """
        Simulate retirement for a specific historical period.

        Args:
            start_year: The year retirement begins
            returns: List of annual returns for the period
            inflation_rates: List of annual inflation rates

        Returns:
            Dictionary with simulation results for this period
        """
        from .data import SP500_RETURNS, BOND_RETURNS, INFLATION_RATES

        portfolio = self.portfolio_value

        # Calculate initial withdrawal
        if self.withdrawal_amount:
            initial_withdrawal = self.withdrawal_amount
        else:
            initial_withdrawal = self.portfolio_value * self.withdrawal_rate

        current_withdrawal = initial_withdrawal
        total_withdrawals = 0
        yearly_values = [portfolio]
        yearly_details = []  # Detailed year-by-year breakdown
        depleted_year = None

        for year in range(self.years_in_retirement):
            current_age = self.retirement_age + year
            calendar_year = start_year + year
            annual_return = returns[year] if year < len(returns) else 0.07
            inflation = inflation_rates[year] if year < len(inflation_rates) else 0.03

            # Get individual stock and bond returns for this year
            stock_return = SP500_RETURNS.get(calendar_year, 0.07)
            bond_return = BOND_RETURNS.get(calendar_year, 0.04)
            actual_inflation = INFLATION_RATES.get(calendar_year, 0.03)

            portfolio_start = portfolio

            # Apply market return
            investment_gain = portfolio * annual_return
            portfolio = portfolio + investment_gain

            # Calculate net withdrawal (reduce by SS and pension if applicable)
            gross_withdrawal = current_withdrawal
            net_withdrawal = current_withdrawal
            ss_income = 0
            pension_income = 0

            # Social Security kicks in at specified age
            if self.social_security_annual > 0:
                ss_start = self.social_security_start_age or 67
                if current_age >= ss_start:
                    ss_income = self.social_security_annual
                    net_withdrawal = max(0, net_withdrawal - ss_income)

            # Pension reduces withdrawal need
            if self.pension_annual > 0:
                pension_income = self.pension_annual
                net_withdrawal = max(0, net_withdrawal - pension_income)

            # Make withdrawal
            portfolio = portfolio - net_withdrawal
            total_withdrawals += net_withdrawal

            # Track depletion
            if portfolio <= 0:
                portfolio = 0
                if depleted_year is None:
                    depleted_year = year + 1

            # Record detailed year data
            yearly_details.append({
                'year': year + 1,
                'calendar_year': calendar_year,
                'age': current_age,
                'portfolio_start': portfolio_start,
                'stock_return': stock_return * 100,
                'bond_return': bond_return * 100,
                'blended_return': annual_return * 100,
                'investment_gain': investment_gain,
                'inflation_rate': actual_inflation * 100,
                'gross_withdrawal': gross_withdrawal,
                'social_security': ss_income,
                'pension': pension_income,
                'net_withdrawal': net_withdrawal,
                'portfolio_end': portfolio,
                'year_change': portfolio - portfolio_start,
                'year_change_pct': ((portfolio - portfolio_start) / portfolio_start * 100) if portfolio_start > 0 else 0,
            })

            yearly_values.append(portfolio)

            # Adjust withdrawal for inflation
            current_withdrawal = current_withdrawal * (1 + inflation)

        success = depleted_year is None
        avg_return = sum(returns) / len(returns) if returns else 0

        return {
            'start_year': start_year,
            'end_year': start_year + self.years_in_retirement - 1,
            'success': success,
            'years_lasted': depleted_year if depleted_year else self.years_in_retirement,
            'final_portfolio_value': portfolio,
            'total_withdrawals': total_withdrawals,
            'average_return': avg_return * 100,
            'yearly_values': yearly_values,
            'yearly_details': yearly_details,
        }

    def _analyze_vulnerable_periods(self, failed_periods: List[Dict]) -> List[Dict]:
        """
        Analyze failed periods to identify vulnerability patterns.

        Args:
            failed_periods: List of period results that failed

        Returns:
            List of vulnerable period descriptions
        """
        if not failed_periods:
            return []

        vulnerable = []
        for period in sorted(failed_periods, key=lambda x: x['start_year']):
            vulnerable.append({
                'start_year': period['start_year'],
                'end_year': period['end_year'],
                'years_lasted': period['years_lasted'],
                'shortfall_years': self.years_in_retirement - period['years_lasted'],
                'reason': self._identify_failure_reason(period),
            })

        return vulnerable

    def _identify_failure_reason(self, period: Dict) -> str:
        """Identify the likely reason for period failure."""
        start_year = period['start_year']

        # Check for known difficult periods
        if 1973 <= start_year <= 1974:
            return "Stagflation: High inflation combined with poor market returns"
        elif 2000 <= start_year <= 2002:
            return "Dot-com bust followed by poor early returns"
        elif start_year == 2007 or start_year == 2008:
            return "Great Financial Crisis caused severe early losses"
        elif period['average_return'] < 4:
            return "Below-average returns throughout retirement period"
        else:
            return "Sequence of returns risk: Poor early-year performance"

    def _test_notable_periods(self, notable_periods: Dict) -> List[Dict]:
        """
        Test retirement starting in notable historical periods.

        Args:
            notable_periods: Dictionary of notable period definitions

        Returns:
            List of results for each notable period
        """
        from .data import get_returns_for_period, get_inflation_for_period

        results = []
        for period_name, period_info in notable_periods.items():
            start_year = period_info['start_year']

            # Only test if we have enough data
            try:
                returns = get_returns_for_period(start_year, self.years_in_retirement, self.stock_allocation)
                inflation = get_inflation_for_period(start_year, self.years_in_retirement)

                result = self._simulate_period(start_year, returns, inflation)
                results.append({
                    'period_name': period_name.replace('_', ' ').title(),
                    'description': period_info['description'],
                    'start_year': start_year,
                    'success': result['success'],
                    'years_lasted': result['years_lasted'],
                    'final_portfolio_value': result['final_portfolio_value'],
                })
            except (KeyError, IndexError):
                # Not enough data for this period
                continue

        return results

    def _calculate_yearly_percentiles(self, period_results: List[Dict]) -> List[Dict]:
        """
        Calculate percentiles for each year across all periods.

        Args:
            period_results: List of all period simulation results

        Returns:
            List of yearly percentile data for charting
        """
        yearly_percentiles = []

        for year in range(self.years_in_retirement + 1):
            year_values = []
            for result in period_results:
                if year < len(result['yearly_values']):
                    year_values.append(result['yearly_values'][year])

            if year_values:
                yearly_percentiles.append({
                    'year': year,
                    'age': self.retirement_age + year,
                    'p5': float(np.percentile(year_values, 5)),
                    'p10': float(np.percentile(year_values, 10)),
                    'p25': float(np.percentile(year_values, 25)),
                    'p50': float(np.percentile(year_values, 50)),
                    'p75': float(np.percentile(year_values, 75)),
                    'p90': float(np.percentile(year_values, 90)),
                    'p95': float(np.percentile(year_values, 95)),
                    'mean': float(np.mean(year_values)),
                })

        return yearly_percentiles
