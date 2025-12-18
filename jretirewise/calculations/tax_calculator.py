"""
Tax Calculator for jRetireWise.

Implements federal income tax calculations, Social Security taxation,
capital gains treatment, NIIT, Medicare surcharges, and state tax
calculations for retirement planning scenarios.

Based on 2025 IRS tax brackets and regulations.
"""

from decimal import Decimal
from typing import Dict, Tuple, Optional


class TaxCalculator:
    """
    Calculate federal and state income taxes for retirement scenarios.

    Implements 2025 IRS tax brackets, Social Security taxation rules,
    capital gains treatment, NIIT, and state tax calculations.
    """

    # 2025 Federal Tax Brackets (IRS Published Rates)
    FEDERAL_TAX_BRACKETS_2025 = {
        'single': [
            (Decimal('11600'), Decimal('0.10')),
            (Decimal('47150'), Decimal('0.12')),
            (Decimal('100525'), Decimal('0.22')),
            (Decimal('191950'), Decimal('0.24')),
            (Decimal('243725'), Decimal('0.32')),
            (Decimal('609350'), Decimal('0.35')),
            (Decimal('inf'), Decimal('0.37')),
        ],
        'mfj': [  # Married Filing Jointly
            (Decimal('23200'), Decimal('0.10')),
            (Decimal('94300'), Decimal('0.12')),
            (Decimal('201050'), Decimal('0.22')),
            (Decimal('383900'), Decimal('0.24')),
            (Decimal('487450'), Decimal('0.32')),
            (Decimal('731200'), Decimal('0.35')),
            (Decimal('inf'), Decimal('0.37')),
        ],
        'mfs': [  # Married Filing Separately
            (Decimal('11600'), Decimal('0.10')),
            (Decimal('47150'), Decimal('0.12')),
            (Decimal('100525'), Decimal('0.22')),
            (Decimal('191950'), Decimal('0.24')),
            (Decimal('243725'), Decimal('0.32')),
            (Decimal('365600'), Decimal('0.35')),
            (Decimal('inf'), Decimal('0.37')),
        ],
        'hoh': [  # Head of Household
            (Decimal('16550'), Decimal('0.10')),
            (Decimal('63100'), Decimal('0.12')),
            (Decimal('100500'), Decimal('0.22')),
            (Decimal('191950'), Decimal('0.24')),
            (Decimal('243700'), Decimal('0.32')),
            (Decimal('609350'), Decimal('0.35')),
            (Decimal('inf'), Decimal('0.37')),
        ],
    }

    # 2025 Standard Deductions
    STANDARD_DEDUCTION_2025 = {
        'single': Decimal('14600'),
        'mfj': Decimal('29200'),
        'mfs': Decimal('14600'),
        'hoh': Decimal('21900'),
        'qw': Decimal('29200'),  # Qualifying Widow(er)
    }

    # 2025 Long-Term Capital Gains Brackets
    CAPITAL_GAINS_BRACKETS_2025 = {
        'single': [
            (Decimal('47025'), Decimal('0.00')),   # 0% up to $47,025
            (Decimal('518900'), Decimal('0.15')),  # 15% up to $518,900
            (Decimal('inf'), Decimal('0.20')),     # 20% above
        ],
        'mfj': [
            (Decimal('94050'), Decimal('0.00')),   # 0% up to $94,050
            (Decimal('583750'), Decimal('0.15')),  # 15% up to $583,750
            (Decimal('inf'), Decimal('0.20')),     # 20% above
        ],
        'mfs': [
            (Decimal('47025'), Decimal('0.00')),
            (Decimal('291850'), Decimal('0.15')),
            (Decimal('inf'), Decimal('0.20')),
        ],
        'hoh': [
            (Decimal('63000'), Decimal('0.00')),
            (Decimal('551350'), Decimal('0.15')),
            (Decimal('inf'), Decimal('0.20')),
        ],
    }

    # NIIT (Net Investment Income Tax) Thresholds
    NIIT_THRESHOLD_2025 = {
        'single': Decimal('200000'),
        'mfj': Decimal('250000'),
        'mfs': Decimal('125000'),
        'hoh': Decimal('200000'),
        'qw': Decimal('250000'),
    }
    NIIT_RATE = Decimal('0.038')  # 3.8%

    # Medicare IRMAA Thresholds (2025)
    # Additional Medicare premiums based on MAGI
    IRMAA_BRACKETS_2025 = {
        'single': [
            (Decimal('106000'), Decimal('0')),
            (Decimal('133000'), Decimal('76.40')),
            (Decimal('167000'), Decimal('190.90')),
            (Decimal('200000'), Decimal('305.50')),
            (Decimal('500000'), Decimal('420.00')),
            (Decimal('inf'), Decimal('472.90')),
        ],
        'mfj': [
            (Decimal('212000'), Decimal('0')),
            (Decimal('266000'), Decimal('76.40')),
            (Decimal('334000'), Decimal('190.90')),
            (Decimal('400000'), Decimal('305.50')),
            (Decimal('750000'), Decimal('420.00')),
            (Decimal('inf'), Decimal('472.90')),
        ],
    }

    def __init__(
        self,
        filing_status: str = 'single',
        state_of_residence: str = '',
        year: int = 2025
    ):
        """
        Initialize TaxCalculator.

        Args:
            filing_status: Filing status (single, mfj, mfs, hoh, qw)
            state_of_residence: State code for state tax calculation
            year: Tax year (currently only 2025 supported)
        """
        self.filing_status = filing_status
        self.state = state_of_residence
        self.year = year

        # Validate filing status
        if filing_status not in self.FEDERAL_TAX_BRACKETS_2025:
            raise ValueError(
                f"Invalid filing status: {filing_status}. "
                f"Must be one of: {list(self.FEDERAL_TAX_BRACKETS_2025.keys())}"
            )

    def calculate_federal_tax(
        self,
        ordinary_income: Decimal,
        capital_gains: Decimal = Decimal('0'),
        deductions: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate federal income tax liability.

        Args:
            ordinary_income: Ordinary taxable income (wages, IRA distributions, etc.)
            capital_gains: Long-term capital gains income
            deductions: Total deductions (defaults to standard deduction)

        Returns:
            Federal tax liability
        """
        # Apply deductions
        if deductions is None:
            deductions = self.STANDARD_DEDUCTION_2025[self.filing_status]

        # Calculate taxable ordinary income
        taxable_ordinary_income = max(Decimal('0'), ordinary_income - deductions)

        # Calculate tax on ordinary income
        ordinary_tax = self._apply_tax_brackets(
            taxable_ordinary_income,
            self.FEDERAL_TAX_BRACKETS_2025[self.filing_status]
        )

        # Calculate tax on capital gains
        capital_gains_tax = self._apply_tax_brackets(
            capital_gains,
            self.CAPITAL_GAINS_BRACKETS_2025[self.filing_status]
        )

        return ordinary_tax + capital_gains_tax

    def calculate_social_security_taxable_amount(
        self,
        social_security_benefits: Decimal,
        other_income: Decimal
    ) -> Decimal:
        """
        Calculate the taxable portion of Social Security benefits.

        Uses the IRS formula to determine if 0%, 50%, or 85% of
        Social Security benefits are subject to taxation.

        Args:
            social_security_benefits: Total Social Security benefits received
            other_income: Other taxable income (wages, IRA distributions, etc.)

        Returns:
            Taxable portion of Social Security benefits
        """
        # Provisional income = other income + 50% of SS benefits
        provisional_income = other_income + (social_security_benefits * Decimal('0.5'))

        # Thresholds for taxation
        if self.filing_status == 'mfj':
            first_threshold = Decimal('32000')
            second_threshold = Decimal('44000')
        else:  # single, mfs, hoh
            first_threshold = Decimal('25000')
            second_threshold = Decimal('34000')

        # No Social Security is taxable if below first threshold
        if provisional_income <= first_threshold:
            return Decimal('0')

        # Up to 50% taxable if between first and second threshold
        elif provisional_income <= second_threshold:
            amount_over_first = provisional_income - first_threshold
            return min(
                amount_over_first,
                social_security_benefits * Decimal('0.5')
            )

        # Up to 85% taxable if above second threshold
        else:
            # First tier: 50% of benefits up to second threshold
            first_tier = min(
                second_threshold - first_threshold,
                social_security_benefits * Decimal('0.5')
            )

            # Second tier: 85% of amount over second threshold
            amount_over_second = provisional_income - second_threshold
            second_tier = min(
                amount_over_second * Decimal('0.85'),
                social_security_benefits * Decimal('0.85') - first_tier
            )

            return first_tier + second_tier

    def calculate_niit(
        self,
        investment_income: Decimal,
        magi: Decimal
    ) -> Decimal:
        """
        Calculate Net Investment Income Tax (NIIT).

        NIIT is 3.8% on net investment income for taxpayers
        with MAGI above certain thresholds.

        Args:
            investment_income: Net investment income (capital gains, dividends, etc.)
            magi: Modified Adjusted Gross Income

        Returns:
            NIIT liability
        """
        threshold = self.NIIT_THRESHOLD_2025.get(
            self.filing_status,
            self.NIIT_THRESHOLD_2025['single']
        )

        if magi <= threshold:
            return Decimal('0')

        # NIIT applies to lesser of:
        # 1. Net investment income, or
        # 2. Amount by which MAGI exceeds threshold
        amount_over_threshold = magi - threshold
        taxable_amount = min(investment_income, amount_over_threshold)

        return taxable_amount * self.NIIT_RATE

    def calculate_medicare_surcharge(self, magi: Decimal) -> Decimal:
        """
        Calculate Medicare IRMAA (Income-Related Monthly Adjustment Amount) surcharge.

        Higher-income retirees pay additional Medicare premiums based on MAGI.
        Returns annual additional premium.

        Args:
            magi: Modified Adjusted Gross Income

        Returns:
            Annual Medicare IRMAA surcharge
        """
        brackets = self.IRMAA_BRACKETS_2025.get(
            self.filing_status,
            self.IRMAA_BRACKETS_2025['single']
        )

        monthly_surcharge = Decimal('0')

        for threshold, surcharge in brackets:
            if magi <= threshold:
                monthly_surcharge = surcharge
                break

        # Return annual amount (monthly * 12)
        return Decimal(str(monthly_surcharge)) * Decimal('12')

    def calculate_state_tax(
        self,
        agi: Decimal,
        state_code: Optional[str] = None
    ) -> Decimal:
        """
        Calculate state income tax.

        Currently implements California as an example.
        Other states can be added via plugin pattern.

        Args:
            agi: Adjusted Gross Income
            state_code: State code (defaults to self.state)

        Returns:
            State tax liability
        """
        state = (state_code or self.state).upper()

        if not state or state == 'NONE':
            return Decimal('0')

        # California tax calculation (example)
        if state == 'CA':
            return self._calculate_california_tax(agi)

        # Texas, Florida, Nevada, etc. - no state income tax
        elif state in ['TX', 'FL', 'NV', 'WA', 'WY', 'SD', 'TN', 'NH', 'AK']:
            return Decimal('0')

        # Default: estimate 5% flat tax for unknown states
        else:
            return agi * Decimal('0.05')

    def _calculate_california_tax(self, agi: Decimal) -> Decimal:
        """
        Calculate California state income tax (2025 brackets).

        Args:
            agi: Adjusted Gross Income

        Returns:
            California state tax liability
        """
        # 2025 California tax brackets (Single filer example)
        # TODO: Add brackets for all filing statuses
        if self.filing_status in ['single', 'mfs']:
            ca_brackets = [
                (Decimal('10412'), Decimal('0.01')),
                (Decimal('24684'), Decimal('0.02')),
                (Decimal('38959'), Decimal('0.04')),
                (Decimal('54081'), Decimal('0.06')),
                (Decimal('68350'), Decimal('0.08')),
                (Decimal('349137'), Decimal('0.093')),
                (Decimal('418961'), Decimal('0.103')),
                (Decimal('698271'), Decimal('0.113')),
                (Decimal('inf'), Decimal('0.123')),
            ]
        else:  # MFJ
            ca_brackets = [
                (Decimal('20824'), Decimal('0.01')),
                (Decimal('49368'), Decimal('0.02')),
                (Decimal('77918'), Decimal('0.04')),
                (Decimal('108162'), Decimal('0.06')),
                (Decimal('136700'), Decimal('0.08')),
                (Decimal('698274'), Decimal('0.093')),
                (Decimal('837922'), Decimal('0.103')),
                (Decimal('1000000'), Decimal('0.113')),
                (Decimal('inf'), Decimal('0.123')),
            ]

        # Apply CA standard deduction
        ca_standard_deduction = Decimal('5202') if self.filing_status in ['single', 'mfs'] else Decimal('10404')
        taxable_income = max(Decimal('0'), agi - ca_standard_deduction)

        return self._apply_tax_brackets(taxable_income, ca_brackets)

    def _apply_tax_brackets(
        self,
        income: Decimal,
        brackets: list
    ) -> Decimal:
        """
        Apply progressive tax brackets to income.

        Args:
            income: Taxable income
            brackets: List of (threshold, rate) tuples

        Returns:
            Total tax liability
        """
        tax = Decimal('0')
        previous_threshold = Decimal('0')

        for threshold, rate in brackets:
            if income <= previous_threshold:
                break

            # Calculate taxable amount in this bracket
            if income <= threshold:
                taxable_in_bracket = income - previous_threshold
            else:
                taxable_in_bracket = threshold - previous_threshold

            # Add tax for this bracket
            tax += taxable_in_bracket * rate

            previous_threshold = threshold

            if income <= threshold:
                break

        return tax

    def calculate_total_tax_liability(
        self,
        ordinary_income: Decimal,
        capital_gains: Decimal = Decimal('0'),
        social_security_benefits: Decimal = Decimal('0'),
        deductions: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate comprehensive tax liability including all components.

        Args:
            ordinary_income: Ordinary taxable income
            capital_gains: Long-term capital gains
            social_security_benefits: Social Security benefits received
            deductions: Total deductions (defaults to standard deduction)

        Returns:
            Dictionary with tax breakdown:
            {
                'federal_tax': Decimal,
                'state_tax': Decimal,
                'niit': Decimal,
                'medicare_surcharge': Decimal,
                'total_tax': Decimal,
                'agi': Decimal,
                'magi': Decimal,
                'effective_rate': Decimal (as percentage)
            }
        """
        # Calculate taxable portion of Social Security
        ss_taxable = self.calculate_social_security_taxable_amount(
            social_security_benefits,
            ordinary_income
        )

        # Calculate AGI (includes taxable SS)
        agi = ordinary_income + capital_gains + ss_taxable

        # MAGI = AGI (simplified; in reality may include add-backs)
        magi = agi

        # Calculate federal tax
        federal_tax = self.calculate_federal_tax(
            ordinary_income + ss_taxable,
            capital_gains,
            deductions
        )

        # Calculate NIIT (on investment income only)
        niit = self.calculate_niit(capital_gains, magi)

        # Calculate Medicare surcharge
        medicare_surcharge = self.calculate_medicare_surcharge(magi)

        # Calculate state tax
        state_tax = self.calculate_state_tax(agi)

        # Total tax
        total_tax = federal_tax + state_tax + niit + medicare_surcharge

        # Effective tax rate
        effective_rate = (total_tax / agi * Decimal('100')) if agi > 0 else Decimal('0')

        return {
            'federal_tax': federal_tax,
            'state_tax': state_tax,
            'niit': niit,
            'medicare_surcharge': medicare_surcharge,
            'total_tax': total_tax,
            'agi': agi,
            'magi': magi,
            'effective_rate': effective_rate,
            'social_security_taxable': ss_taxable,
        }
