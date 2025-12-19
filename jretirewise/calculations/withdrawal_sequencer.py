"""
Withdrawal Sequencer for jRetireWise.

Implements withdrawal sequencing strategies to minimize taxes by determining
the optimal order and amounts to withdraw from different account types
(Taxable, Traditional IRA/401k, Roth, HSA).

Supports strategies like Taxable-First, Tax-Deferred-First, Roth-First,
Optimized, and Custom allocation.
"""

from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from jretirewise.calculations.tax_calculator import TaxCalculator


class WithdrawalSequencer:
    """
    Optimize withdrawal sequences to minimize tax liability.

    Compares different withdrawal strategies and calculates year-by-year
    tax impact for different account sequencing approaches.
    """

    # IRS Uniform Lifetime Table for RMD calculations (2024+)
    RMD_LIFE_EXPECTANCY_TABLE = {
        72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
        78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7,
        84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9,
        90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1, 94: 9.5, 95: 8.9,
        96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0,
        102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3, 107: 4.1,
        108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1,
        114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3,
        120: 2.0,
    }

    def __init__(
        self,
        tax_profile: 'TaxProfile',
        scenario: 'RetirementScenario'
    ):
        """
        Initialize WithdrawalSequencer.

        Args:
            tax_profile: User's tax profile with filing status and state
            scenario: Retirement scenario with parameters
        """
        self.tax_profile = tax_profile
        self.scenario = scenario

        # Get account balances from user's portfolio
        balances = tax_profile.get_account_balances_from_portfolio()
        self.traditional_balance = float(balances['traditional'])
        self.roth_balance = float(balances['roth'])
        self.taxable_balance = float(balances['taxable'])
        self.hsa_balance = float(balances['hsa'])

        # Initialize tax calculator
        self.tax_calc = TaxCalculator(
            filing_status=tax_profile.filing_status,
            state_of_residence=tax_profile.state_of_residence
        )

    def calculate_rmd(
        self,
        age: int,
        account_balance: Decimal,
        rmd_age: int = 73
    ) -> Decimal:
        """
        Calculate Required Minimum Distribution (RMD).

        RMDs begin at age 73 (as of 2024) for Traditional IRA/401k.

        Args:
            age: Current age
            account_balance: Traditional IRA/401k balance
            rmd_age: Age at which RMDs begin (default 73)

        Returns:
            Required minimum distribution amount (0 if age < rmd_age)
        """
        if age < rmd_age:
            return Decimal('0')

        # Get life expectancy factor from IRS table
        life_expectancy = self.RMD_LIFE_EXPECTANCY_TABLE.get(
            age,
            Decimal('2.0')  # Default for ages beyond table
        )

        # RMD = account balance / life expectancy factor
        rmd = account_balance / Decimal(str(life_expectancy))

        return rmd

    def execute_strategy(
        self,
        strategy_type: str,
        annual_withdrawal_need: Decimal,
        retirement_age: int,
        life_expectancy: int,
        social_security_annual: Decimal = Decimal('0'),
        pension_annual: Decimal = Decimal('0'),
        custom_percentages: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Execute a withdrawal strategy and calculate year-by-year tax impact.

        Args:
            strategy_type: Strategy type (taxable_first, tax_deferred_first, etc.)
            annual_withdrawal_need: Annual withdrawal amount needed
            retirement_age: Age at retirement
            life_expectancy: Life expectancy age
            social_security_annual: Annual Social Security benefit
            pension_annual: Annual pension income
            custom_percentages: Custom allocation (if strategy_type='custom')

        Returns:
            Dictionary with:
            {
                'strategy_type': str,
                'total_tax_paid': Decimal,
                'effective_tax_rate': Decimal,
                'year_by_year': List[Dict],
                'final_balances': Dict,
            }
        """
        # Initialize account balances
        traditional = Decimal(str(self.traditional_balance))
        roth = Decimal(str(self.roth_balance))
        taxable = Decimal(str(self.taxable_balance))
        hsa = Decimal(str(self.hsa_balance))

        years_in_retirement = life_expectancy - retirement_age
        year_by_year_results = []
        total_tax_paid = Decimal('0')

        for year in range(1, years_in_retirement + 1):
            current_age = retirement_age + year - 1

            # Calculate RMD if applicable
            rmd_amount = self.calculate_rmd(current_age, traditional, rmd_age=73)

            # Determine withdrawal amounts by account type
            withdrawal_plan = self._determine_withdrawal_amounts(
                strategy_type=strategy_type,
                total_need=annual_withdrawal_need,
                traditional_balance=traditional,
                roth_balance=roth,
                taxable_balance=taxable,
                hsa_balance=hsa,
                rmd_amount=rmd_amount,
                custom_percentages=custom_percentages
            )

            # Calculate taxes for this year
            tax_result = self._calculate_year_taxes(
                withdrawal_plan=withdrawal_plan,
                social_security_annual=social_security_annual,
                pension_annual=pension_annual,
                age=current_age
            )

            # Update account balances
            traditional -= withdrawal_plan['traditional']
            traditional = max(Decimal('0'), traditional)

            roth -= withdrawal_plan['roth']
            roth = max(Decimal('0'), roth)

            taxable -= withdrawal_plan['taxable']
            taxable = max(Decimal('0'), taxable)

            hsa -= withdrawal_plan['hsa']
            hsa = max(Decimal('0'), hsa)

            # Apply growth to remaining balances (simplified 7% growth)
            growth_rate = Decimal('0.07')
            traditional *= (Decimal('1') + growth_rate)
            roth *= (Decimal('1') + growth_rate)
            taxable *= (Decimal('1') + growth_rate)
            hsa *= (Decimal('1') + growth_rate)

            # Store year results
            year_result = {
                'year': year,
                'age': current_age,
                'withdrawal_plan': {
                    'traditional': float(withdrawal_plan['traditional']),
                    'roth': float(withdrawal_plan['roth']),
                    'taxable': float(withdrawal_plan['taxable']),
                    'hsa': float(withdrawal_plan['hsa']),
                    'total': float(withdrawal_plan['total']),
                },
                'tax_liability': {
                    'federal_tax': float(tax_result['federal_tax']),
                    'state_tax': float(tax_result['state_tax']),
                    'niit': float(tax_result['niit']),
                    'medicare_surcharge': float(tax_result['medicare_surcharge']),
                    'total_tax': float(tax_result['total_tax']),
                    'effective_rate': float(tax_result['effective_rate']),
                },
                'balances_end_of_year': {
                    'traditional': float(traditional),
                    'roth': float(roth),
                    'taxable': float(taxable),
                    'hsa': float(hsa),
                    'total': float(traditional + roth + taxable + hsa),
                },
                'rmd_amount': float(rmd_amount),
            }

            year_by_year_results.append(year_result)
            total_tax_paid += tax_result['total_tax']

            # Stop if all accounts depleted
            if traditional + roth + taxable + hsa <= 0:
                break

        # Calculate average effective tax rate
        total_income = annual_withdrawal_need * Decimal(str(len(year_by_year_results)))
        avg_effective_rate = (total_tax_paid / total_income * Decimal('100')) if total_income > 0 else Decimal('0')

        return {
            'strategy_type': strategy_type,
            'total_tax_paid': float(total_tax_paid),
            'effective_tax_rate': float(avg_effective_rate),
            'year_by_year': year_by_year_results,
            'final_balances': {
                'traditional': float(traditional),
                'roth': float(roth),
                'taxable': float(taxable),
                'hsa': float(hsa),
                'total': float(traditional + roth + taxable + hsa),
            },
        }

    def _determine_withdrawal_amounts(
        self,
        strategy_type: str,
        total_need: Decimal,
        traditional_balance: Decimal,
        roth_balance: Decimal,
        taxable_balance: Decimal,
        hsa_balance: Decimal,
        rmd_amount: Decimal = Decimal('0'),
        custom_percentages: Optional[Dict[str, float]] = None
    ) -> Dict[str, Decimal]:
        """
        Determine how much to withdraw from each account type.

        Args:
            strategy_type: Withdrawal strategy
            total_need: Total annual withdrawal needed
            traditional_balance: Traditional IRA balance
            roth_balance: Roth balance
            taxable_balance: Taxable account balance
            hsa_balance: HSA balance
            rmd_amount: Required RMD (forces Traditional withdrawal)
            custom_percentages: Custom allocation percentages

        Returns:
            Dictionary with withdrawal amounts by account type
        """
        # Start with RMD if required
        remaining_need = total_need
        traditional_withdrawal = rmd_amount
        remaining_need -= rmd_amount

        roth_withdrawal = Decimal('0')
        taxable_withdrawal = Decimal('0')
        hsa_withdrawal = Decimal('0')

        if remaining_need <= 0:
            return {
                'traditional': traditional_withdrawal,
                'roth': roth_withdrawal,
                'taxable': taxable_withdrawal,
                'hsa': hsa_withdrawal,
                'total': traditional_withdrawal,
            }

        # Apply strategy
        if strategy_type == 'taxable_first':
            # Withdraw from taxable first, then traditional, then Roth
            taxable_withdrawal = min(remaining_need, taxable_balance)
            remaining_need -= taxable_withdrawal

            if remaining_need > 0:
                traditional_withdrawal += min(remaining_need, traditional_balance - traditional_withdrawal)
                remaining_need -= (traditional_withdrawal - rmd_amount)

            if remaining_need > 0:
                roth_withdrawal = min(remaining_need, roth_balance)

        elif strategy_type == 'tax_deferred_first':
            # Withdraw from traditional first (tax-deferred), then taxable, then Roth
            traditional_withdrawal = min(remaining_need + rmd_amount, traditional_balance)
            remaining_need -= (traditional_withdrawal - rmd_amount)

            if remaining_need > 0:
                taxable_withdrawal = min(remaining_need, taxable_balance)
                remaining_need -= taxable_withdrawal

            if remaining_need > 0:
                roth_withdrawal = min(remaining_need, roth_balance)

        elif strategy_type == 'roth_first':
            # Withdraw from Roth first (tax-free), then taxable, then traditional
            roth_withdrawal = min(remaining_need, roth_balance)
            remaining_need -= roth_withdrawal

            if remaining_need > 0:
                taxable_withdrawal = min(remaining_need, taxable_balance)
                remaining_need -= taxable_withdrawal

            if remaining_need > 0:
                traditional_withdrawal += min(remaining_need, traditional_balance - traditional_withdrawal)

        elif strategy_type == 'optimized':
            # Optimized: Fill up to 12% bracket with Traditional, rest from Taxable/Roth
            # This is a simplified optimization - full optimization would require iterating
            # For now, use a heuristic: minimize taxable income while preserving Roth growth

            # Fill lower tax brackets with Traditional withdrawals
            bracket_12_threshold = Decimal('94300')  # MFJ example
            traditional_withdrawal = min(
                remaining_need,
                traditional_balance,
                bracket_12_threshold / Decimal('2')  # Conservative estimate
            )
            remaining_need -= traditional_withdrawal

            # Use taxable for the rest (long-term cap gains often taxed at 0% or 15%)
            if remaining_need > 0:
                taxable_withdrawal = min(remaining_need, taxable_balance)
                remaining_need -= taxable_withdrawal

            # Preserve Roth for last (tax-free growth)
            if remaining_need > 0:
                roth_withdrawal = min(remaining_need, roth_balance)

        elif strategy_type == 'custom' and custom_percentages:
            # Custom allocation by percentage
            taxable_pct = Decimal(str(custom_percentages.get('taxable', 0.0)))
            traditional_pct = Decimal(str(custom_percentages.get('traditional', 0.0)))
            roth_pct = Decimal(str(custom_percentages.get('roth', 0.0)))
            hsa_pct = Decimal(str(custom_percentages.get('hsa', 0.0)))

            taxable_withdrawal = min(remaining_need * taxable_pct, taxable_balance)
            traditional_add = min(remaining_need * traditional_pct, traditional_balance - traditional_withdrawal)
            traditional_withdrawal += traditional_add
            roth_withdrawal = min(remaining_need * roth_pct, roth_balance)
            hsa_withdrawal = min(remaining_need * hsa_pct, hsa_balance)

        return {
            'traditional': traditional_withdrawal,
            'roth': roth_withdrawal,
            'taxable': taxable_withdrawal,
            'hsa': hsa_withdrawal,
            'total': traditional_withdrawal + roth_withdrawal + taxable_withdrawal + hsa_withdrawal,
        }

    def _calculate_year_taxes(
        self,
        withdrawal_plan: Dict[str, Decimal],
        social_security_annual: Decimal,
        pension_annual: Decimal,
        age: int
    ) -> Dict[str, Decimal]:
        """
        Calculate taxes for a single year based on withdrawal plan.

        Args:
            withdrawal_plan: Withdrawal amounts by account type
            social_security_annual: Social Security benefits for the year
            pension_annual: Pension income for the year
            age: Current age

        Returns:
            Dictionary with tax liability breakdown
        """
        # Ordinary income = Traditional IRA withdrawals + pension
        ordinary_income = withdrawal_plan['traditional'] + pension_annual

        # Capital gains = portion of taxable account withdrawals
        # Assume 80% cost basis, 20% gains (simplified)
        capital_gains = withdrawal_plan['taxable'] * Decimal('0.20')

        # Calculate taxes using TaxCalculator
        tax_result = self.tax_calc.calculate_total_tax_liability(
            ordinary_income=ordinary_income,
            capital_gains=capital_gains,
            social_security_benefits=social_security_annual
        )

        return tax_result

    def compare_strategies(
        self,
        strategies: List[str],
        annual_withdrawal_need: Decimal,
        retirement_age: int,
        life_expectancy: int,
        social_security_annual: Decimal = Decimal('0'),
        pension_annual: Decimal = Decimal('0')
    ) -> List[Dict]:
        """
        Compare multiple withdrawal strategies side-by-side.

        Args:
            strategies: List of strategy types to compare
            annual_withdrawal_need: Annual withdrawal amount
            retirement_age: Retirement age
            life_expectancy: Life expectancy
            social_security_annual: Social Security benefits
            pension_annual: Pension income

        Returns:
            List of strategy results, sorted by total_tax_paid (lowest first)
        """
        results = []

        for strategy_type in strategies:
            result = self.execute_strategy(
                strategy_type=strategy_type,
                annual_withdrawal_need=annual_withdrawal_need,
                retirement_age=retirement_age,
                life_expectancy=life_expectancy,
                social_security_annual=social_security_annual,
                pension_annual=pension_annual
            )
            results.append(result)

        # Sort by total tax paid (lowest first)
        results.sort(key=lambda x: x['total_tax_paid'])

        return results
