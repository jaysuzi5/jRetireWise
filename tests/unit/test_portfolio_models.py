"""
Unit tests for Phase 2.0 Advanced Portfolio Management models.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.financial.models import Portfolio, Account, AccountValueHistory, PortfolioSnapshot


class PortfolioModelTestCase(TestCase):
    """Tests for Portfolio model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )

    def test_portfolio_creation(self):
        """Test portfolio can be created."""
        self.assertEqual(self.portfolio.user, self.user)
        self.assertEqual(self.portfolio.name, 'Test Portfolio')
        self.assertEqual(self.portfolio.description, 'A test portfolio')

    def test_portfolio_default_name(self):
        """Test portfolio default name."""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        portfolio = Portfolio.objects.create(user=user2)
        self.assertEqual(portfolio.name, 'My Portfolio')

    def test_portfolio_str_representation(self):
        """Test portfolio string representation."""
        self.assertEqual(str(self.portfolio), 'Portfolio: Test Portfolio')

    def test_portfolio_total_value_empty(self):
        """Test total value with no accounts."""
        total = self.portfolio.get_total_value()
        self.assertEqual(total, Decimal('0.00'))

    def test_portfolio_total_value_single_account(self):
        """Test total value with one account."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Savings',
            current_value=Decimal('10000.00'),
            status='active'
        )
        total = self.portfolio.get_total_value()
        self.assertEqual(total, Decimal('10000.00'))

    def test_portfolio_total_value_multiple_accounts(self):
        """Test total value with multiple accounts."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Savings',
            current_value=Decimal('10000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='roth_ira',
            account_name='Roth IRA',
            current_value=Decimal('50000.00'),
            status='active'
        )
        total = self.portfolio.get_total_value()
        self.assertEqual(total, Decimal('60000.00'))

    def test_portfolio_total_value_excludes_closed_accounts(self):
        """Test that closed accounts are excluded from total."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Active Savings',
            current_value=Decimal('10000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Closed Savings',
            current_value=Decimal('5000.00'),
            status='closed'
        )
        total = self.portfolio.get_total_value()
        self.assertEqual(total, Decimal('10000.00'))

    def test_portfolio_accounts_by_type(self):
        """Test grouping accounts by type."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Savings 1',
            current_value=Decimal('10000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Savings 2',
            current_value=Decimal('5000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='roth_ira',
            account_name='Roth IRA',
            current_value=Decimal('50000.00'),
            status='active'
        )

        by_type = self.portfolio.get_accounts_by_type()
        self.assertIn('Savings Account', by_type)
        self.assertIn('Roth IRA', by_type)
        self.assertEqual(len(by_type['Savings Account']['accounts']), 2)
        self.assertEqual(by_type['Savings Account']['total_value'], Decimal('15000.00'))
        self.assertEqual(len(by_type['Roth IRA']['accounts']), 1)
        self.assertEqual(by_type['Roth IRA']['total_value'], Decimal('50000.00'))


class AccountModelTestCase(TestCase):
    """Tests for Account model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Test Savings',
            account_number='SAV123',
            institution_name='Test Bank',
            current_value=Decimal('10000.00'),
            default_growth_rate=Decimal('0.07'),
            inflation_adjustment=Decimal('0.02'),
            expected_contribution_rate=Decimal('0.05'),
            tax_treatment='post_tax',
            rmd_age=72,
            status='active'
        )

    def test_account_creation(self):
        """Test account can be created."""
        self.assertEqual(self.account.portfolio, self.portfolio)
        self.assertEqual(self.account.account_type, 'savings')
        self.assertEqual(self.account.account_name, 'Test Savings')
        self.assertEqual(self.account.current_value, Decimal('10000.00'))

    def test_account_str_representation(self):
        """Test account string representation."""
        expected = f"Test Savings (Savings Account)"
        self.assertEqual(str(self.account), expected)

    def test_account_default_values(self):
        """Test account default values."""
        account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Minimal Account'
        )
        self.assertEqual(account.current_value, Decimal('0.00'))
        self.assertEqual(account.default_growth_rate, Decimal('0.07'))
        self.assertEqual(account.inflation_adjustment, Decimal('0.00'))
        self.assertEqual(account.expected_contribution_rate, Decimal('0.00'))
        self.assertEqual(account.tax_treatment, 'pre_tax')
        self.assertEqual(account.status, 'active')
        self.assertEqual(account.withdrawal_priority, 0)

    def test_effective_growth_rate_calculation(self):
        """Test effective growth rate calculation."""
        rate = self.account.get_effective_growth_rate()
        expected = Decimal('0.07') - Decimal('0.02')
        self.assertEqual(rate, expected)

    def test_annual_contribution_calculation(self):
        """Test annual contribution calculation."""
        contribution = self.account.get_annual_contribution()
        expected = Decimal('10000.00') * Decimal('0.05')
        self.assertEqual(contribution, expected)

    def test_penalty_free_withdrawal_age_check(self):
        """Test penalty-free withdrawal age check."""
        self.account.withdrawal_restrictions = {'min_age': 59.5}
        self.account.save()

        self.assertTrue(self.account.is_penalty_free_withdrawal_age(60))
        self.assertFalse(self.account.is_penalty_free_withdrawal_age(59))
        self.assertTrue(self.account.is_penalty_free_withdrawal_age(59.5))

    def test_penalty_free_withdrawal_no_restrictions(self):
        """Test penalty-free withdrawal with no restrictions."""
        # When no restrictions are set, function returns False
        self.assertFalse(self.account.is_penalty_free_withdrawal_age(50))

    def test_investment_allocation_validation(self):
        """Test investment allocation JSON field."""
        account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='taxable_brokerage',
            account_name='Brokerage',
            investment_allocation={'stocks': 60, 'bonds': 30, 'other': 10}
        )
        self.assertEqual(account.investment_allocation['stocks'], 60)
        self.assertEqual(account.investment_allocation['bonds'], 30)
        self.assertEqual(account.investment_allocation['other'], 10)

    def test_withdrawal_priority_ordering(self):
        """Test account ordering by withdrawal priority."""
        # Create accounts with different withdrawal priorities
        acc1 = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='First',
            withdrawal_priority=1
        )
        acc2 = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Second',
            withdrawal_priority=2
        )
        acc3 = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Third',
            withdrawal_priority=0
        )

        # Filter out the account from setUp (Test Savings)
        accounts = list(self.portfolio.accounts.filter(
            account_name__in=['First', 'Second', 'Third']
        ))
        # Should be ordered by withdrawal_priority, then by account_name
        self.assertEqual(accounts[0].withdrawal_priority, 0)
        self.assertEqual(accounts[1].withdrawal_priority, 1)
        self.assertEqual(accounts[2].withdrawal_priority, 2)

    def test_account_status_choices(self):
        """Test account status choices."""
        for status, _ in Account.STATUS_CHOICES:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type='savings',
                account_name=f'Account {status}',
                status=status
            )
            self.assertEqual(account.status, status)

    def test_account_tax_treatment_choices(self):
        """Test tax treatment choices."""
        for treatment, _ in Account.TAX_TREATMENT:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type='savings',
                account_name=f'Account {treatment}',
                tax_treatment=treatment
            )
            self.assertEqual(account.tax_treatment, treatment)


class AccountValueHistoryTestCase(TestCase):
    """Tests for AccountValueHistory model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Test Savings'
        )

    def test_history_creation(self):
        """Test account history can be created."""
        from datetime import date
        history = AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('10000.00'),
            recorded_date=date.today(),
            recorded_by=self.user,
            source='manual',
            notes='Initial deposit'
        )
        self.assertEqual(history.account, self.account)
        self.assertEqual(history.value, Decimal('10000.00'))
        self.assertEqual(history.recorded_by, self.user)

    def test_history_str_representation(self):
        """Test history string representation."""
        from datetime import date
        history = AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('10000.00'),
            recorded_date=date.today(),
            recorded_by=self.user
        )
        expected = f"Test Savings - $10,000.00 on {date.today()}"
        self.assertEqual(str(history), expected)

    def test_history_ordering(self):
        """Test history is ordered by recorded_date descending."""
        from datetime import date, timedelta
        date1 = date.today()
        date2 = date1 - timedelta(days=1)
        date3 = date1 - timedelta(days=2)

        AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('10000.00'),
            recorded_date=date1,
            recorded_by=self.user
        )
        AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('9000.00'),
            recorded_date=date2,
            recorded_by=self.user
        )
        AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('8000.00'),
            recorded_date=date3,
            recorded_by=self.user
        )

        histories = list(self.account.value_history.all())
        self.assertEqual(histories[0].value, Decimal('10000.00'))  # most recent
        self.assertEqual(histories[1].value, Decimal('9000.00'))
        self.assertEqual(histories[2].value, Decimal('8000.00'))  # oldest

    def test_history_source_choices(self):
        """Test history source field choices."""
        from datetime import date
        for source, _ in [('manual', 'Manual Entry'), ('import', 'CSV Import'), ('system', 'System Generated')]:
            history = AccountValueHistory.objects.create(
                account=self.account,
                value=Decimal('1000.00'),
                recorded_date=date.today(),
                recorded_by=self.user,
                source=source
            )
            self.assertEqual(history.source, source)


class PortfolioSnapshotTestCase(TestCase):
    """Tests for PortfolioSnapshot model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(user=self.user)

    def test_snapshot_creation(self):
        """Test snapshot can be created."""
        from datetime import date
        snapshot = PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('50000.00'),
            snapshot_date=date.today(),
            calculated_from='all_accounts',
            notes='Monthly snapshot'
        )
        self.assertEqual(snapshot.portfolio, self.portfolio)
        self.assertEqual(snapshot.total_value, Decimal('50000.00'))

    def test_snapshot_str_representation(self):
        """Test snapshot string representation."""
        from datetime import date
        snapshot = PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('50000.00'),
            snapshot_date=date.today()
        )
        expected = f"Portfolio Snapshot - $50,000.00 on {date.today()}"
        self.assertEqual(str(snapshot), expected)

    def test_snapshot_ordering(self):
        """Test snapshots are ordered by snapshot_date descending."""
        from datetime import date, timedelta
        date1 = date.today()
        date2 = date1 - timedelta(days=1)
        date3 = date1 - timedelta(days=2)

        PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('60000.00'),
            snapshot_date=date1
        )
        PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('55000.00'),
            snapshot_date=date2
        )
        PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('50000.00'),
            snapshot_date=date3
        )

        snapshots = list(self.portfolio.snapshots.all())
        self.assertEqual(snapshots[0].total_value, Decimal('60000.00'))  # most recent
        self.assertEqual(snapshots[1].total_value, Decimal('55000.00'))
        self.assertEqual(snapshots[2].total_value, Decimal('50000.00'))  # oldest

    def test_snapshot_calculated_from_choices(self):
        """Test calculated_from field choices."""
        from datetime import date
        for calculated_from, _ in [('all_accounts', 'All Accounts'), ('last_snapshot', 'Last Snapshot')]:
            snapshot = PortfolioSnapshot.objects.create(
                portfolio=self.portfolio,
                total_value=Decimal('50000.00'),
                snapshot_date=date.today(),
                calculated_from=calculated_from
            )
            self.assertEqual(snapshot.calculated_from, calculated_from)


class AccountTypesTestCase(TestCase):
    """Tests for all account types."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.portfolio = Portfolio.objects.create(user=self.user)

    def test_all_retirement_account_types(self):
        """Test all retirement account types can be created."""
        retirement_types = [
            'trad_401k', 'roth_401k', 'trad_ira', 'roth_ira', 'sep_ira', 'solo_401k'
        ]
        for account_type in retirement_types:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type=account_type,
                account_name=f'{account_type} Account'
            )
            self.assertEqual(account.account_type, account_type)

    def test_all_investment_account_types(self):
        """Test all investment account types can be created."""
        investment_types = ['taxable_brokerage', 'joint_account', 'partnership']
        for account_type in investment_types:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type=account_type,
                account_name=f'{account_type} Account'
            )
            self.assertEqual(account.account_type, account_type)

    def test_all_savings_account_types(self):
        """Test all savings account types can be created."""
        savings_types = ['savings', 'hysa', 'money_market']
        for account_type in savings_types:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type=account_type,
                account_name=f'{account_type} Account'
            )
            self.assertEqual(account.account_type, account_type)

    def test_all_health_account_types(self):
        """Test all health-related account types can be created."""
        health_types = ['hsa', 'msa']
        for account_type in health_types:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type=account_type,
                account_name=f'{account_type} Account'
            )
            self.assertEqual(account.account_type, account_type)

    def test_all_other_account_types(self):
        """Test all other account types can be created."""
        other_types = ['529_plan', 'certificate_cd', 'bonds', 'treasuries', 'custom']
        for account_type in other_types:
            account = Account.objects.create(
                portfolio=self.portfolio,
                account_type=account_type,
                account_name=f'{account_type} Account'
            )
            self.assertEqual(account.account_type, account_type)

    def test_total_account_types(self):
        """Test all 19 account types are available."""
        self.assertEqual(len(Account.ACCOUNT_TYPES), 19)
