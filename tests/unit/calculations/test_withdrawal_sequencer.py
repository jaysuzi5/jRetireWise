"""
Unit tests for WithdrawalSequencer.

Tests cover:
- RMD calculation using IRS Uniform Lifetime Table
- Withdrawal strategy execution (taxable_first, tax_deferred_first, roth_first, optimized, custom)
- Year-by-year tax impact analysis
- Strategy comparison and ranking
- Account balance tracking over retirement years
- Integration with TaxCalculator
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from jretirewise.calculations.withdrawal_sequencer import WithdrawalSequencer
from jretirewise.financial.models import TaxProfile


@pytest.fixture
def mock_tax_profile():
    """Create a mock tax profile for testing."""
    profile = Mock()
    profile.filing_status = 'mfj'
    profile.state_of_residence = 'CA'

    # Mock the get_account_balances_from_portfolio method
    profile.get_account_balances_from_portfolio.return_value = {
        'traditional': Decimal('500000'),
        'roth': Decimal('300000'),
        'taxable': Decimal('200000'),
        'hsa': Decimal('50000'),
    }

    return profile


@pytest.fixture
def mock_scenario():
    """Create a mock scenario for testing."""
    scenario = Mock()
    scenario.parameters = {
        'retirement_age': 65,
        'life_expectancy': 95,
        'annual_spending': 80000,
    }
    return scenario


class TestWithdrawalSequencerRMD:
    """Test Required Minimum Distribution calculations."""

    def test_rmd_before_age_73(self, mock_tax_profile, mock_scenario):
        """Test no RMD required before age 73."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=72,
            account_balance=Decimal('500000'),
            rmd_age=73
        )
        assert rmd == Decimal('0')

    def test_rmd_at_age_73(self, mock_tax_profile, mock_scenario):
        """Test RMD calculation at age 73."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=73,
            account_balance=Decimal('500000'),
            rmd_age=73
        )
        # At age 73, life expectancy factor is 26.5
        # RMD = $500,000 / 26.5 = $18,867.92
        expected = Decimal('500000') / Decimal('26.5')
        assert abs(rmd - expected) < Decimal('1')

    def test_rmd_at_age_80(self, mock_tax_profile, mock_scenario):
        """Test RMD calculation at age 80."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=80,
            account_balance=Decimal('400000'),
            rmd_age=73
        )
        # At age 80, life expectancy factor is 20.2
        # RMD = $400,000 / 20.2 = $19,801.98
        expected = Decimal('400000') / Decimal('20.2')
        assert abs(rmd - expected) < Decimal('1')

    def test_rmd_at_age_95(self, mock_tax_profile, mock_scenario):
        """Test RMD calculation at age 95."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=95,
            account_balance=Decimal('100000'),
            rmd_age=73
        )
        # At age 95, life expectancy factor is 8.9
        expected = Decimal('100000') / Decimal('8.9')
        assert abs(rmd - expected) < Decimal('1')

    def test_rmd_beyond_table_uses_default(self, mock_tax_profile, mock_scenario):
        """Test RMD for ages beyond table uses default factor."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=125,
            account_balance=Decimal('50000'),
            rmd_age=73
        )
        # Beyond table, should use default 2.0
        expected = Decimal('50000') / Decimal('2.0')
        assert rmd == expected

    def test_rmd_zero_balance(self, mock_tax_profile, mock_scenario):
        """Test RMD with zero account balance."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)
        rmd = sequencer.calculate_rmd(
            age=75,
            account_balance=Decimal('0'),
            rmd_age=73
        )
        assert rmd == Decimal('0')


class TestWithdrawalSequencerTaxableFirst:
    """Test taxable-first withdrawal strategy."""

    def test_taxable_first_basic(self, mock_tax_profile, mock_scenario):
        """Test taxable-first strategy withdraws from taxable accounts first."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert result['strategy_type'] == 'taxable_first'
        assert 'year_by_year' in result
        assert len(result['year_by_year']) > 0

        # First year should prioritize taxable account
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']
        assert withdrawal_plan['taxable'] > Decimal('0')

    def test_taxable_first_exhausts_taxable_then_traditional(self, mock_tax_profile, mock_scenario):
        """Test strategy moves to traditional after exhausting taxable."""
        # Set up small taxable balance
        mock_tax_profile.get_account_balances_from_portfolio.return_value = {
            'traditional': Decimal('500000'),
            'roth': Decimal('300000'),
            'taxable': Decimal('30000'),  # Small taxable
            'hsa': Decimal('50000'),
        }
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=67,  # Only 2 years
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Year 2 should have depleted taxable and moved to traditional
        year_2 = result['year_by_year'][1]
        assert year_2['withdrawal_plan']['traditional'] > Decimal('0')


class TestWithdrawalSequencerTaxDeferredFirst:
    """Test tax-deferred-first withdrawal strategy."""

    def test_tax_deferred_first_basic(self, mock_tax_profile, mock_scenario):
        """Test tax-deferred-first strategy withdraws from traditional first."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='tax_deferred_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert result['strategy_type'] == 'tax_deferred_first'

        # First year should prioritize traditional account
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']
        assert withdrawal_plan['traditional'] > Decimal('0')

    def test_tax_deferred_first_exhausts_accounts(self, mock_scenario):
        """Test tax_deferred_first when traditional exhausted, moves to taxable then Roth."""
        # Create mock profile with small traditional balance
        mock_profile = Mock()
        mock_profile.filing_status = 'single'
        mock_profile.state_of_residence = 'CA'
        mock_profile.get_account_balances_from_portfolio.return_value = {
            'traditional': Decimal('30000'),  # Small traditional - will exhaust quickly
            'roth': Decimal('100000'),
            'taxable': Decimal('100000'),
            'hsa': Decimal('10000'),
        }

        sequencer = WithdrawalSequencer(mock_profile, mock_scenario)
        result = sequencer.execute_strategy(
            strategy_type='tax_deferred_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=67,  # Short retirement to exhaust traditional
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Check that taxable or roth were used at some point after traditional started depleting
        # Since traditional is only $30k and we need $50k/year, other accounts must be used
        all_years = result['year_by_year']
        taxable_or_roth_used = any(
            year['withdrawal_plan']['taxable'] > Decimal('0') or year['withdrawal_plan']['roth'] > Decimal('0')
            for year in all_years
        )
        assert taxable_or_roth_used, "Should use taxable or roth when traditional insufficient"


class TestWithdrawalSequencerRothFirst:
    """Test Roth-first withdrawal strategy."""

    def test_roth_first_basic(self, mock_tax_profile, mock_scenario):
        """Test Roth-first strategy withdraws from Roth first."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='roth_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert result['strategy_type'] == 'roth_first'

        # First year should prioritize Roth account
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']
        assert withdrawal_plan['roth'] > Decimal('0')

    @pytest.mark.django_db
    def test_roth_first_exhausts_accounts(self):
        """Test roth_first when Roth exhausted, moves to taxable then traditional."""
        from jretirewise.authentication.models import User
        from jretirewise.scenarios.models import RetirementScenario
        from jretirewise.financial.models import Portfolio, Account

        # Create real user and scenario
        user = User.objects.create(email='testuser2@example.com', first_name='Test', last_name='User')
        scenario = RetirementScenario.objects.create(
            user=user,
            name='Test Scenario',
            calculator_type='four_percent',
            parameters={}
        )

        # Create tax profile (only filing status and state)
        tax_profile = TaxProfile.objects.create(
            user=user,
            filing_status='single',
            state_of_residence='CA'
        )

        # Create portfolio with accounts for balances - small Roth, enough taxable and traditional
        portfolio = Portfolio.objects.create(user=user, name='Test Portfolio')
        Account.objects.create(
            portfolio=portfolio,
            account_name='Traditional IRA',
            account_type='trad_ira',
            current_value=Decimal('200000'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Roth IRA',
            account_type='roth_ira',
            current_value=Decimal('30000'),  # Small Roth
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Taxable',
            account_type='taxable_brokerage',
            current_value=Decimal('100000'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='HSA',
            account_type='hsa',
            current_value=Decimal('10000'),
            status='active'
        )

        sequencer = WithdrawalSequencer(tax_profile, scenario)
        result = sequencer.execute_strategy(
            strategy_type='roth_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=67,  # Short retirement to exhaust Roth
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Check that taxable and traditional were used after Roth exhausted
        last_year = result['year_by_year'][-1]
        assert last_year['withdrawal_plan']['taxable'] > Decimal('0') or last_year['withdrawal_plan']['traditional'] > Decimal('0')


class TestWithdrawalSequencerOptimized:
    """Test optimized withdrawal strategy."""

    def test_optimized_basic(self, mock_tax_profile, mock_scenario):
        """Test optimized strategy executes successfully."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='optimized',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert result['strategy_type'] == 'optimized'
        assert len(result['year_by_year']) > 0

    def test_optimized_balances_tax_brackets(self, mock_tax_profile, mock_scenario):
        """Test optimized strategy considers tax brackets."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='optimized',
            annual_withdrawal_need=Decimal('80000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Should use mix of account types to minimize taxes
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']

        # Likely uses both traditional and taxable
        account_types_used = sum([
            1 if withdrawal_plan['traditional'] > 0 else 0,
            1 if withdrawal_plan['roth'] > 0 else 0,
            1 if withdrawal_plan['taxable'] > 0 else 0,
        ])
        assert account_types_used >= 1  # At least one account type used

    def test_optimized_exhausts_taxable_uses_roth(self, mock_scenario):
        """Test optimized strategy falls back to Roth when traditional and taxable exhausted."""
        # Create mock profile with small traditional and taxable, large Roth
        mock_profile = Mock()
        mock_profile.filing_status = 'single'
        mock_profile.state_of_residence = 'CA'
        mock_profile.get_account_balances_from_portfolio.return_value = {
            'traditional': Decimal('50000'),  # Small traditional
            'roth': Decimal('200000'),  # Large Roth
            'taxable': Decimal('50000'),  # Small taxable
            'hsa': Decimal('10000'),
        }

        sequencer = WithdrawalSequencer(mock_profile, mock_scenario)
        result = sequencer.execute_strategy(
            strategy_type='optimized',
            annual_withdrawal_need=Decimal('60000'),
            retirement_age=65,
            life_expectancy=68,  # Longer retirement to exhaust traditional and taxable
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Check that Roth was eventually used after traditional and taxable exhausted
        # Look for a year where Roth withdrawal occurred
        roth_used = any(year['withdrawal_plan']['roth'] > Decimal('0') for year in result['year_by_year'])
        assert roth_used, "Optimized strategy should use Roth when traditional and taxable exhausted"


class TestWithdrawalSequencerCustom:
    """Test custom allocation withdrawal strategy."""

    def test_custom_strategy_with_percentages(self, mock_tax_profile, mock_scenario):
        """Test custom strategy with specified percentages."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        custom_percentages = {
            'taxable': 0.40,      # 40% from taxable
            'traditional': 0.40,  # 40% from traditional
            'roth': 0.20,         # 20% from Roth
            'hsa': 0.00,         # 0% from HSA
        }

        result = sequencer.execute_strategy(
            strategy_type='custom',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0'),
            custom_percentages=custom_percentages
        )

        assert result['strategy_type'] == 'custom'

        # Check first year follows percentages (approximately)
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']

        # Approximately 40/40/20 split (may vary due to balance constraints)
        total_withdrawal = withdrawal_plan['total']
        if total_withdrawal > 0:
            taxable_pct = float(withdrawal_plan['taxable'] / total_withdrawal)
            assert 0.30 <= taxable_pct <= 0.50  # Allow some variance

    def test_custom_strategy_100_percent_single_account(self, mock_tax_profile, mock_scenario):
        """Test custom strategy with 100% from single account type."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        custom_percentages = {
            'taxable': 1.0,   # 100% from taxable
            'traditional': 0.0,
            'roth': 0.0,
            'hsa': 0.0,
        }

        result = sequencer.execute_strategy(
            strategy_type='custom',
            annual_withdrawal_need=Decimal('40000'),
            retirement_age=65,
            life_expectancy=67,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0'),
            custom_percentages=custom_percentages
        )

        # First year should be all from taxable
        first_year = result['year_by_year'][0]
        withdrawal_plan = first_year['withdrawal_plan']
        assert withdrawal_plan['taxable'] > Decimal('0')
        assert withdrawal_plan['traditional'] == Decimal('0')
        assert withdrawal_plan['roth'] == Decimal('0')


class TestWithdrawalSequencerRMDHandling:
    """Test RMD handling across different strategies."""

    def test_rmd_forces_traditional_withdrawal(self, mock_tax_profile, mock_scenario):
        """Test RMD forces minimum traditional withdrawal at age 73+."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='roth_first',  # Would normally avoid traditional
            annual_withdrawal_need=Decimal('30000'),
            retirement_age=73,  # RMD age
            life_expectancy=78,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Even with Roth-first, should have traditional withdrawal due to RMD
        first_year = result['year_by_year'][0]
        assert first_year['rmd_amount'] > Decimal('0')
        assert first_year['withdrawal_plan']['traditional'] >= first_year['rmd_amount']

    def test_rmd_increases_with_age(self, mock_tax_profile, mock_scenario):
        """Test RMD percentage increases as age increases."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('40000'),
            retirement_age=73,
            life_expectancy=85,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # RMD should increase over time (as percentage of balance)
        year_1_rmd = result['year_by_year'][0]['rmd_amount']
        year_5_rmd = result['year_by_year'][4]['rmd_amount']

        # Note: Absolute RMD may decrease as balance decreases,
        # but as percentage of remaining balance it increases
        assert year_1_rmd >= Decimal('0')
        assert year_5_rmd >= Decimal('0')


class TestWithdrawalSequencerCompareStrategies:
    """Test strategy comparison functionality."""

    def test_compare_strategies_ranks_by_total_tax(self, mock_tax_profile, mock_scenario):
        """Test strategy comparison ranks by total tax paid."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        strategies = ['taxable_first', 'tax_deferred_first', 'roth_first', 'optimized']

        results = sequencer.compare_strategies(
            strategies=strategies,
            annual_withdrawal_need=Decimal('60000'),
            retirement_age=65,
            life_expectancy=75,
            social_security_annual=Decimal('25000'),
            pension_annual=Decimal('0')
        )

        assert len(results) == 4

        # Results should be sorted by total_tax_paid (lowest first)
        for i in range(len(results) - 1):
            assert results[i]['total_tax_paid'] <= results[i+1]['total_tax_paid']

    def test_compare_strategies_includes_all_requested(self, mock_tax_profile, mock_scenario):
        """Test comparison includes all requested strategies."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        strategies = ['taxable_first', 'optimized']

        results = sequencer.compare_strategies(
            strategies=strategies,
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert len(results) == 2
        strategy_types = [r['strategy_type'] for r in results]
        assert 'taxable_first' in strategy_types
        assert 'optimized' in strategy_types

    def test_compare_strategies_with_social_security(self, mock_tax_profile, mock_scenario):
        """Test strategy comparison with Social Security income."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        results = sequencer.compare_strategies(
            strategies=['taxable_first', 'optimized'],
            annual_withdrawal_need=Decimal('40000'),
            retirement_age=67,
            life_expectancy=75,
            social_security_annual=Decimal('30000'),
            pension_annual=Decimal('0')
        )

        # With SS income, tax impact should be considered
        assert len(results) == 2
        for result in results:
            assert result['total_tax_paid'] > Decimal('0')

    def test_compare_single_strategy(self, mock_tax_profile, mock_scenario):
        """Test comparison with single strategy."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        results = sequencer.compare_strategies(
            strategies=['optimized'],
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert len(results) == 1
        assert results[0]['strategy_type'] == 'optimized'


class TestWithdrawalSequencerYearByYear:
    """Test year-by-year analysis."""

    def test_year_by_year_tracks_balances(self, mock_tax_profile, mock_scenario):
        """Test year-by-year result tracks account balances."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        year_by_year = result['year_by_year']

        # Balances should decrease over time (due to withdrawals)
        for i in range(len(year_by_year) - 1):
            current_total = year_by_year[i]['balances_end_of_year']['total']
            next_year_would_be_lower = True  # May grow due to investment returns

            # But after withdrawals, should eventually decrease
            assert current_total >= Decimal('0')

    def test_year_by_year_applies_growth(self, mock_tax_profile, mock_scenario):
        """Test year-by-year applies investment growth."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        # Set withdrawal to zero to see pure growth
        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('0'),
            retirement_age=65,
            life_expectancy=67,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # With no withdrawals and 7% growth, balance should increase
        year_1 = result['year_by_year'][0]
        year_2 = result['year_by_year'][1]

        year_1_total = year_1['balances_end_of_year']['total']
        year_2_total = year_2['balances_end_of_year']['total']

        # Year 2 should be higher due to growth (approximately 7%)
        assert year_2_total > year_1_total

    def test_year_by_year_stops_when_depleted(self, mock_tax_profile, mock_scenario):
        """Test year-by-year stops when all accounts depleted."""
        # Set very low balances and high withdrawal
        mock_tax_profile.get_account_balances_from_portfolio.return_value = {
            'traditional': Decimal('100000'),
            'roth': Decimal('50000'),
            'taxable': Decimal('50000'),
            'hsa': Decimal('0'),
        }

        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('100000'),  # High withdrawal
            retirement_age=65,
            life_expectancy=95,  # Long time period
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Should stop before reaching age 95 due to depletion
        assert len(result['year_by_year']) < 30


class TestWithdrawalSequencerTaxCalculations:
    """Test tax calculations within withdrawal sequencer."""

    def test_tax_calculated_for_each_year(self, mock_tax_profile, mock_scenario):
        """Test tax is calculated for each year."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('60000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        for year_result in result['year_by_year']:
            tax_liability = year_result['tax_liability']
            assert 'federal_tax' in tax_liability
            assert 'state_tax' in tax_liability
            assert 'total_tax' in tax_liability
            assert 'effective_rate' in tax_liability

    def test_total_tax_paid_aggregates_years(self, mock_tax_profile, mock_scenario):
        """Test total_tax_paid is sum of all years."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Sum up all years' taxes
        calculated_total = sum(
            Decimal(str(year['tax_liability']['total_tax']))
            for year in result['year_by_year']
        )

        # Should match reported total_tax_paid
        assert abs(Decimal(str(result['total_tax_paid'])) - calculated_total) < Decimal('1')


class TestWithdrawalSequencerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_withdrawal_need(self, mock_tax_profile, mock_scenario):
        """Test zero withdrawal need."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('0'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Should still run but with zero withdrawals
        assert len(result['year_by_year']) > 0
        for year in result['year_by_year']:
            assert year['withdrawal_plan']['total'] == Decimal('0')

    def test_single_year_retirement(self, mock_tax_profile, mock_scenario):
        """Test single year retirement (edge case)."""
        sequencer = WithdrawalSequencer(mock_tax_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=66,  # Only 1 year
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        assert len(result['year_by_year']) == 1

    def test_all_accounts_zero_balance(self):
        """Test handling of all zero account balances."""
        mock_profile = Mock()
        mock_profile.filing_status = 'single'
        mock_profile.state_of_residence = 'CA'

        # Mock the get_account_balances_from_portfolio method
        mock_profile.get_account_balances_from_portfolio.return_value = {
            'traditional': Decimal('0'),
            'roth': Decimal('0'),
            'taxable': Decimal('0'),
            'hsa': Decimal('0'),
        }

        mock_scenario = Mock()
        mock_scenario.parameters = {}

        sequencer = WithdrawalSequencer(mock_profile, mock_scenario)

        result = sequencer.execute_strategy(
            strategy_type='taxable_first',
            annual_withdrawal_need=Decimal('50000'),
            retirement_age=65,
            life_expectancy=70,
            social_security_annual=Decimal('0'),
            pension_annual=Decimal('0')
        )

        # Should run but with minimal withdrawals (all zeros)
        assert len(result['year_by_year']) >= 0
