"""
Unit tests for TaxCalculator.

Tests cover:
- Federal income tax calculation (2025 brackets)
- Long-term capital gains tax (0%, 15%, 20%)
- Social Security taxation (0%, 50%, 85%)
- NIIT (Net Investment Income Tax)
- Medicare IRMAA surcharges
- State tax calculation (California)
- Total tax liability calculation
"""

import pytest
from decimal import Decimal
from jretirewise.calculations.tax_calculator import TaxCalculator


class TestTaxCalculatorFederalIncomeTax:
    """Test federal income tax calculations for all filing statuses."""

    def test_single_filer_10_percent_bracket(self):
        """Test single filer in 10% bracket."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        tax = calc.calculate_federal_income_tax(Decimal('10000'))
        # First $11,600 at 10% = $1,160, but only $10k income
        assert tax == Decimal('1000.00')

    def test_single_filer_multiple_brackets(self):
        """Test single filer spanning multiple brackets."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $50,000 income spans 10% and 12% brackets
        tax = calc.calculate_federal_income_tax(Decimal('50000'))
        # $11,600 at 10% = $1,160
        # $38,400 at 12% = $4,608
        # Total = $5,768
        assert tax == Decimal('5768.00')

    def test_married_filing_jointly_brackets(self):
        """Test married filing jointly brackets."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        # $100,000 income spans 10% and 12% brackets
        tax = calc.calculate_federal_income_tax(Decimal('100000'))
        # $23,200 at 10% = $2,320
        # $76,800 at 12% = $9,216
        # Total = $11,536
        assert tax == Decimal('11536.00')

    def test_head_of_household_brackets(self):
        """Test head of household brackets."""
        calc = TaxCalculator(filing_status='hoh', state_of_residence='CA')
        tax = calc.calculate_federal_income_tax(Decimal('50000'))
        # Should use HoH brackets
        assert tax > Decimal('0')

    def test_married_filing_separately_brackets(self):
        """Test married filing separately brackets."""
        calc = TaxCalculator(filing_status='mfs', state_of_residence='CA')
        tax = calc.calculate_federal_income_tax(Decimal('50000'))
        # Should use MFS brackets (same as single)
        assert tax > Decimal('0')

    def test_zero_income(self):
        """Test zero income results in zero tax."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        tax = calc.calculate_federal_income_tax(Decimal('0'))
        assert tax == Decimal('0')

    def test_high_income_top_bracket(self):
        """Test high income reaching 37% bracket."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $600,000 should reach 37% bracket
        tax = calc.calculate_federal_income_tax(Decimal('600000'))
        assert tax > Decimal('150000')  # Substantial tax at high income


class TestTaxCalculatorCapitalGains:
    """Test long-term capital gains tax calculations."""

    def test_capital_gains_zero_percent_single(self):
        """Test 0% capital gains for low income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $30,000 ordinary income + $10,000 gains = $40,000 total
        # Should be in 0% cap gains bracket
        tax = calc.calculate_capital_gains_tax(
            capital_gains=Decimal('10000'),
            ordinary_income=Decimal('30000')
        )
        assert tax == Decimal('0')

    def test_capital_gains_fifteen_percent_single(self):
        """Test 15% capital gains for middle income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $50,000 ordinary + $20,000 gains = $70,000
        # Should be in 15% cap gains bracket
        tax = calc.calculate_capital_gains_tax(
            capital_gains=Decimal('20000'),
            ordinary_income=Decimal('50000')
        )
        assert tax == Decimal('3000.00')  # 15% of $20,000

    def test_capital_gains_twenty_percent_single(self):
        """Test 20% capital gains for high income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # High income should trigger 20% rate
        tax = calc.calculate_capital_gains_tax(
            capital_gains=Decimal('50000'),
            ordinary_income=Decimal('500000')
        )
        assert tax == Decimal('10000.00')  # 20% of $50,000

    def test_capital_gains_zero_percent_mfj(self):
        """Test 0% capital gains for married filing jointly."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        # MFJ has higher 0% threshold ($96,700)
        tax = calc.calculate_capital_gains_tax(
            capital_gains=Decimal('15000'),
            ordinary_income=Decimal('70000')
        )
        assert tax == Decimal('0')

    def test_capital_gains_mixed_brackets(self):
        """Test capital gains spanning 0% and 15% brackets."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # Ordinary income near threshold, gains span both 0% and 15%
        tax = calc.calculate_capital_gains_tax(
            capital_gains=Decimal('20000'),
            ordinary_income=Decimal('38000')  # Close to $48,350 threshold
        )
        # Part at 0%, part at 15%
        assert tax >= Decimal('0') and tax <= Decimal('3000')


class TestTaxCalculatorSocialSecurity:
    """Test Social Security benefit taxation."""

    def test_ss_no_taxation_single_low_income(self):
        """Test 0% SS taxation for low income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('20000'),
            other_income=Decimal('10000')
        )
        # Provisional income = $10k + $10k (50% of SS) = $20k
        # Below $25k threshold for single
        assert taxable == Decimal('0')

    def test_ss_fifty_percent_taxation_single(self):
        """Test up to 50% SS taxation for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('30000'),
            other_income=Decimal('20000')
        )
        # Provisional income = $20k + $15k = $35k
        # Between $25k and $34k, up to 50% taxable
        assert taxable > Decimal('0')
        assert taxable <= Decimal('15000')  # Max 50% of $30k

    def test_ss_eighty_five_percent_taxation_single(self):
        """Test up to 85% SS taxation for high income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('30000'),
            other_income=Decimal('50000')
        )
        # Provisional income = $50k + $15k = $65k
        # Above $34k threshold, up to 85% taxable
        assert taxable > Decimal('15000')  # More than 50%
        assert taxable <= Decimal('25500')  # Max 85% of $30k

    def test_ss_no_taxation_mfj_low_income(self):
        """Test 0% SS taxation for married filing jointly."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('30000'),
            other_income=Decimal('15000')
        )
        # Provisional income = $15k + $15k = $30k
        # Below $32k threshold for MFJ
        assert taxable == Decimal('0')

    def test_ss_eighty_five_percent_taxation_mfj(self):
        """Test up to 85% SS taxation for high income MFJ."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('40000'),
            other_income=Decimal('80000')
        )
        # Provisional income = $80k + $20k = $100k
        # Well above $44k threshold, up to 85% taxable
        assert taxable <= Decimal('34000')  # Max 85% of $40k

    def test_ss_zero_benefits(self):
        """Test zero SS benefits."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            ss_benefits=Decimal('0'),
            other_income=Decimal('50000')
        )
        assert taxable == Decimal('0')


class TestTaxCalculatorNIIT:
    """Test Net Investment Income Tax (3.8% on investment income)."""

    def test_niit_below_threshold_single(self):
        """Test no NIIT below MAGI threshold for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        niit = calc.calculate_niit(
            investment_income=Decimal('10000'),
            magi=Decimal('150000')
        )
        # Below $200k threshold
        assert niit == Decimal('0')

    def test_niit_above_threshold_single(self):
        """Test NIIT above MAGI threshold for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        niit = calc.calculate_niit(
            investment_income=Decimal('50000'),
            magi=Decimal('250000')
        )
        # MAGI exceeds threshold by $50k
        # NIIT on lesser of investment income or excess MAGI
        # 3.8% of $50k = $1,900
        assert niit == Decimal('1900.00')

    def test_niit_above_threshold_mfj(self):
        """Test NIIT above MAGI threshold for married filing jointly."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        niit = calc.calculate_niit(
            investment_income=Decimal('100000'),
            magi=Decimal('300000')
        )
        # MFJ threshold is $250k
        # Excess is $50k, investment income is $100k
        # NIIT on $50k = 3.8% * $50k = $1,900
        assert niit == Decimal('1900.00')

    def test_niit_limited_by_investment_income(self):
        """Test NIIT limited by investment income amount."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        niit = calc.calculate_niit(
            investment_income=Decimal('10000'),
            magi=Decimal('300000')
        )
        # Excess MAGI is $100k, but investment income only $10k
        # NIIT on $10k = 3.8% * $10k = $380
        assert niit == Decimal('380.00')

    def test_niit_zero_investment_income(self):
        """Test no NIIT with zero investment income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        niit = calc.calculate_niit(
            investment_income=Decimal('0'),
            magi=Decimal('300000')
        )
        assert niit == Decimal('0')


class TestTaxCalculatorMedicareSurcharge:
    """Test Medicare IRMAA surcharges."""

    def test_medicare_no_surcharge_below_threshold(self):
        """Test no Medicare surcharge below MAGI threshold."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('100000'))
        # Below all thresholds
        assert surcharge == Decimal('0')

    def test_medicare_surcharge_single_tier_1(self):
        """Test Medicare surcharge tier 1 for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('110000'))
        # First surcharge tier for single
        assert surcharge > Decimal('0')

    def test_medicare_surcharge_single_highest_tier(self):
        """Test Medicare surcharge highest tier for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('600000'))
        # Highest surcharge tier
        assert surcharge > Decimal('5000')

    def test_medicare_surcharge_mfj_tier_1(self):
        """Test Medicare surcharge tier 1 for married filing jointly."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('220000'))
        # First surcharge tier for MFJ
        assert surcharge > Decimal('0')


class TestTaxCalculatorStateTax:
    """Test state income tax calculations."""

    def test_california_state_tax_low_income(self):
        """Test California state tax for low income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        state_tax = calc.calculate_state_tax(income=Decimal('30000'))
        # California has progressive brackets
        assert state_tax > Decimal('0')
        assert state_tax < Decimal('3000')  # Should be under 10%

    def test_california_state_tax_high_income(self):
        """Test California state tax for high income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        state_tax = calc.calculate_state_tax(income=Decimal('500000'))
        # California top bracket is 13.3%
        assert state_tax > Decimal('50000')

    def test_no_state_tax_for_non_ca(self):
        """Test no state tax for non-California states (not yet implemented)."""
        calc = TaxCalculator(filing_status='single', state_of_residence='TX')
        state_tax = calc.calculate_state_tax(income=Decimal('100000'))
        # Texas has no state income tax
        assert state_tax == Decimal('0')

    def test_state_tax_zero_income(self):
        """Test zero state tax for zero income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        state_tax = calc.calculate_state_tax(income=Decimal('0'))
        assert state_tax == Decimal('0')


class TestTaxCalculatorTotalLiability:
    """Test total tax liability calculation integrating all components."""

    def test_total_tax_simple_case(self):
        """Test total tax liability with simple case."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('50000'),
            capital_gains=Decimal('0'),
            social_security_benefits=Decimal('0')
        )

        # Should have federal and state tax
        assert result['federal_tax'] > Decimal('0')
        assert result['state_tax'] > Decimal('0')
        assert result['total_tax'] == (
            result['federal_tax'] +
            result['state_tax'] +
            result['niit'] +
            result['medicare_surcharge']
        )
        assert result['effective_rate'] > Decimal('0')

    def test_total_tax_with_capital_gains(self):
        """Test total tax liability with capital gains."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('50000'),
            capital_gains=Decimal('20000'),
            social_security_benefits=Decimal('0')
        )

        # Should include cap gains tax
        assert result['total_tax'] > Decimal('0')
        assert result['agi'] == Decimal('50000')  # Ordinary income only
        assert result['magi'] == Decimal('70000')  # Includes cap gains

    def test_total_tax_with_social_security(self):
        """Test total tax liability with Social Security benefits."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('40000'),
            capital_gains=Decimal('0'),
            social_security_benefits=Decimal('30000')
        )

        # Should include taxable portion of SS
        assert result['total_tax'] > Decimal('0')
        assert result['agi'] > Decimal('40000')  # Includes taxable SS

    def test_total_tax_high_income_with_niit(self):
        """Test total tax liability with NIIT for high earner."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('150000'),
            capital_gains=Decimal('100000'),
            social_security_benefits=Decimal('0')
        )

        # Should trigger NIIT
        assert result['niit'] > Decimal('0')
        assert result['total_tax'] > Decimal('50000')

    def test_total_tax_very_high_income_medicare(self):
        """Test total tax with Medicare surcharge for very high earner."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('500000'),
            capital_gains=Decimal('200000'),
            social_security_benefits=Decimal('40000')
        )

        # Should trigger Medicare surcharge
        assert result['medicare_surcharge'] > Decimal('0')
        assert result['total_tax'] > Decimal('150000')

    def test_total_tax_effective_rate_calculation(self):
        """Test effective tax rate calculation."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('100000'),
            capital_gains=Decimal('0'),
            social_security_benefits=Decimal('0')
        )

        # Effective rate should be total tax / total income * 100
        expected_rate = (result['total_tax'] / Decimal('100000')) * Decimal('100')
        assert abs(result['effective_rate'] - expected_rate) < Decimal('0.01')

    def test_total_tax_zero_income(self):
        """Test zero tax liability for zero income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('0'),
            capital_gains=Decimal('0'),
            social_security_benefits=Decimal('0')
        )

        assert result['federal_tax'] == Decimal('0')
        assert result['state_tax'] == Decimal('0')
        assert result['niit'] == Decimal('0')
        assert result['medicare_surcharge'] == Decimal('0')
        assert result['total_tax'] == Decimal('0')
        assert result['effective_rate'] == Decimal('0')


class TestTaxCalculatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_negative_income_raises_error_or_treats_as_zero(self):
        """Test handling of negative income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # Implementation may treat negative as zero or raise error
        try:
            tax = calc.calculate_federal_income_tax(Decimal('-1000'))
            assert tax == Decimal('0')
        except ValueError:
            # Also acceptable to raise error for negative income
            pass

    def test_very_large_income(self):
        """Test handling of very large income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('10000000'),
            capital_gains=Decimal('0'),
            social_security_benefits=Decimal('0')
        )

        # Should handle large numbers correctly
        assert result['total_tax'] > Decimal('3000000')

    def test_decimal_precision(self):
        """Test decimal precision is maintained."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        result = calc.calculate_total_tax_liability(
            ordinary_income=Decimal('50000.50'),
            capital_gains=Decimal('10000.75'),
            social_security_benefits=Decimal('0')
        )

        # Result should maintain decimal precision
        assert isinstance(result['total_tax'], Decimal)
        assert result['total_tax'].as_tuple().exponent == -2  # Two decimal places

    def test_all_filing_statuses_valid(self):
        """Test all filing statuses are valid."""
        statuses = ['single', 'mfj', 'mfs', 'hoh']
        for status in statuses:
            calc = TaxCalculator(filing_status=status, state_of_residence='CA')
            result = calc.calculate_total_tax_liability(
                ordinary_income=Decimal('50000'),
                capital_gains=Decimal('0'),
                social_security_benefits=Decimal('0')
            )
            assert result['total_tax'] > Decimal('0')
