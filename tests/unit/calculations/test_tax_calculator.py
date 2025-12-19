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


class TestTaxCalculatorFederalTax:
    """Test federal tax calculations for all filing statuses."""

    def test_single_filer_low_income(self):
        """Test single filer with low income (10% bracket)."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $30,000 income - $14,600 standard deduction = $15,400 taxable
        # $11,600 at 10% + $3,800 at 12% = $1,160 + $456 = $1,616
        tax = calc.calculate_federal_tax(ordinary_income=Decimal('30000'))
        assert tax > Decimal('1000')
        assert tax < Decimal('2000')

    def test_single_filer_multiple_brackets(self):
        """Test single filer spanning multiple brackets."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $75,000 income should span multiple brackets
        tax = calc.calculate_federal_tax(ordinary_income=Decimal('75000'))
        assert tax > Decimal('8000')
        assert tax < Decimal('12000')

    def test_married_filing_jointly(self):
        """Test married filing jointly brackets."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        # $100,000 income with MFJ standard deduction
        tax = calc.calculate_federal_tax(ordinary_income=Decimal('100000'))
        assert tax > Decimal('8000')
        assert tax < Decimal('12000')

    def test_federal_tax_with_capital_gains(self):
        """Test federal tax with capital gains."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # Should calculate tax on both ordinary income and cap gains
        tax = calc.calculate_federal_tax(
            ordinary_income=Decimal('50000'),
            capital_gains=Decimal('10000')
        )
        # Capital gains get preferential treatment (0%, 15%, 20%)
        assert tax > Decimal('3500')
        assert tax < Decimal('6000')

    def test_zero_income(self):
        """Test zero income results in zero tax."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        tax = calc.calculate_federal_tax(ordinary_income=Decimal('0'))
        assert tax == Decimal('0')

    def test_high_income_top_bracket(self):
        """Test high income reaching 37% bracket."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        # $700,000 should reach 37% bracket
        tax = calc.calculate_federal_tax(ordinary_income=Decimal('700000'))
        assert tax > Decimal('200000')


class TestTaxCalculatorSocialSecurity:
    """Test Social Security benefit taxation."""

    def test_ss_no_taxation_single_low_income(self):
        """Test 0% SS taxation for low income single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            social_security_benefits=Decimal('20000'),
            other_income=Decimal('10000')
        )
        # Provisional income = $10k + $10k (50% of SS) = $20k
        # Below $25k threshold for single
        assert taxable == Decimal('0')

    def test_ss_fifty_percent_taxation_single(self):
        """Test up to 50% SS taxation for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            social_security_benefits=Decimal('30000'),
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
            social_security_benefits=Decimal('30000'),
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
            social_security_benefits=Decimal('30000'),
            other_income=Decimal('15000')
        )
        # Provisional income = $15k + $15k = $30k
        # Below $32k threshold for MFJ
        assert taxable == Decimal('0')

    def test_ss_eighty_five_percent_taxation_mfj(self):
        """Test up to 85% SS taxation for high income MFJ."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            social_security_benefits=Decimal('40000'),
            other_income=Decimal('80000')
        )
        # Provisional income = $80k + $20k = $100k
        # Well above $44k threshold, up to 85% taxable
        assert taxable > Decimal('20000')
        assert taxable <= Decimal('34000')  # Max 85% of $40k

    def test_ss_zero_benefits(self):
        """Test zero SS benefits."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        taxable = calc.calculate_social_security_taxable_amount(
            social_security_benefits=Decimal('0'),
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
        # First surcharge tier for single ($106k - $133k)
        # Monthly surcharge $76.40 * 12 = $916.80
        assert surcharge == Decimal('916.80')

    def test_medicare_surcharge_single_highest_tier(self):
        """Test Medicare surcharge highest tier for single filer."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('600000'))
        # Highest surcharge tier: $472.90/month * 12 = $5,674.80
        assert surcharge == Decimal('5674.80')

    def test_medicare_surcharge_mfj_tier_1(self):
        """Test Medicare surcharge tier 1 for married filing jointly."""
        calc = TaxCalculator(filing_status='mfj', state_of_residence='CA')
        surcharge = calc.calculate_medicare_surcharge(magi=Decimal('220000'))
        # First surcharge tier for MFJ ($212k - $266k)
        # Monthly surcharge $76.40 * 12 = $916.80
        assert surcharge == Decimal('916.80')


class TestTaxCalculatorStateTax:
    """Test state income tax calculations."""

    def test_california_state_tax(self):
        """Test California state tax calculation."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        state_tax = calc.calculate_state_tax(agi=Decimal('75000'))
        # California has progressive brackets, should have some tax
        assert state_tax > Decimal('0')
        assert state_tax < Decimal('10000')

    def test_no_state_tax_for_non_ca(self):
        """Test no state tax for non-California states."""
        calc = TaxCalculator(filing_status='single', state_of_residence='TX')
        state_tax = calc.calculate_state_tax(agi=Decimal('100000'))
        # Texas has no state income tax
        assert state_tax == Decimal('0')

    def test_state_tax_zero_income(self):
        """Test zero state tax for zero income."""
        calc = TaxCalculator(filing_status='single', state_of_residence='CA')
        state_tax = calc.calculate_state_tax(agi=Decimal('0'))
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
        assert 'agi' in result
        assert 'magi' in result

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
        # MAGI includes capital gains
        assert result['magi'] >= result['agi']

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
        assert result['agi'] >= Decimal('40000')  # Includes taxable SS

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
        assert result['total_tax'] > Decimal('40000')

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
        assert result['total_tax'] > Decimal('100000')

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
        # Allow small rounding difference
        assert abs(result['effective_rate'] - expected_rate) < Decimal('0.1')

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
            assert result['total_tax'] >= Decimal('0')

    def test_invalid_filing_status_raises_error(self):
        """Test invalid filing status raises ValueError."""
        with pytest.raises(ValueError):
            TaxCalculator(filing_status='invalid', state_of_residence='CA')

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
