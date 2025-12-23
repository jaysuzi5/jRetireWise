"""
Unit tests for TaxProfile model (Phase 2.3.4 - Tax-Aware Withdrawal Calculations).
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.financial.models import TaxProfile, FinancialProfile, Portfolio, Account


class TaxProfileModelTestCase(TestCase):
    """Tests for TaxProfile model."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tax_profile = TaxProfile.objects.create(
            user=self.user,
            filing_status='mfj',
            state_of_residence='CA'
        )
        # Create portfolio with various account types for testing
        self.portfolio = Portfolio.objects.create(user=self.user)

        # Create test accounts
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Traditional 401k',
            account_type='trad_401k',
            current_value=Decimal('250000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Roth IRA',
            account_type='roth_ira',
            current_value=Decimal('100000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Taxable Brokerage',
            account_type='taxable_brokerage',
            current_value=Decimal('150000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Health Savings Account',
            account_type='hsa',
            current_value=Decimal('10000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Savings Account (should be taxable)',
            account_type='savings',
            current_value=Decimal('25000.00'),
            status='active'
        )

    def test_tax_profile_creation(self):
        """Test TaxProfile can be created."""
        self.assertEqual(self.tax_profile.user, self.user)
        self.assertEqual(self.tax_profile.filing_status, 'mfj')
        self.assertEqual(self.tax_profile.state_of_residence, 'CA')

    def test_tax_profile_str_representation(self):
        """Test TaxProfile string representation."""
        self.assertIn(self.user.email, str(self.tax_profile))

    def test_filing_status_choices(self):
        """Test filing status choices are correct."""
        valid_statuses = ['single', 'mfj', 'mfs', 'hoh', 'qw']
        for status in valid_statuses:
            user = User.objects.create_user(
                username=f'user_{status}',
                email=f'{status}@example.com',
                password='testpass123'
            )
            profile = TaxProfile.objects.create(
                user=user,
                filing_status=status
            )
            self.assertEqual(profile.filing_status, status)

    def test_onetoone_relationship_with_user(self):
        """Test TaxProfile has OneToOne relationship with User."""
        # User should only have one tax profile
        self.assertEqual(self.user.tax_profile, self.tax_profile)
        # Creating another tax profile for same user should fail
        with self.assertRaises(Exception):
            TaxProfile.objects.create(user=self.user)

    def test_get_account_balances_from_portfolio(self):
        """Test get_account_balances_from_portfolio returns correct categories."""
        balances = self.tax_profile.get_account_balances_from_portfolio()

        # Verify correct account type categorization
        self.assertEqual(balances['traditional'], Decimal('250000.00'))
        self.assertEqual(balances['roth'], Decimal('100000.00'))
        self.assertEqual(balances['hsa'], Decimal('10000.00'))
        # Taxable should include both taxable_brokerage and savings
        self.assertEqual(balances['taxable'], Decimal('175000.00'))

    def test_get_account_balances_only_includes_active_accounts(self):
        """Test that get_account_balances_from_portfolio only includes active accounts."""
        # Create an inactive account
        Account.objects.create(
            portfolio=self.portfolio,
            account_name='Inactive Account',
            account_type='trad_401k',
            current_value=Decimal('500000.00'),
            status='closed'
        )

        balances = self.tax_profile.get_account_balances_from_portfolio()
        # Should not include the inactive account
        self.assertEqual(balances['traditional'], Decimal('250000.00'))

    def test_get_account_balances_with_no_portfolio(self):
        """Test get_account_balances_from_portfolio when user has no portfolio."""
        # Create a new user with no portfolio
        user_no_portfolio = User.objects.create_user(
            username='noportfolio',
            email='noportfolio@example.com',
            password='testpass123'
        )
        profile = TaxProfile.objects.create(user=user_no_portfolio)

        balances = profile.get_account_balances_from_portfolio()

        # All balances should be zero
        self.assertEqual(balances['traditional'], Decimal('0'))
        self.assertEqual(balances['roth'], Decimal('0'))
        self.assertEqual(balances['taxable'], Decimal('0'))
        self.assertEqual(balances['hsa'], Decimal('0'))

    def test_get_account_balances_with_empty_portfolio(self):
        """Test get_account_balances_from_portfolio with empty portfolio."""
        # Create new user with empty portfolio
        user = User.objects.create_user(
            username='emptyportfolio',
            email='empty@example.com',
            password='testpass123'
        )
        Portfolio.objects.create(user=user)
        profile = TaxProfile.objects.create(user=user)

        balances = profile.get_account_balances_from_portfolio()

        # All balances should be zero
        self.assertEqual(balances['traditional'], Decimal('0'))
        self.assertEqual(balances['roth'], Decimal('0'))
        self.assertEqual(balances['taxable'], Decimal('0'))
        self.assertEqual(balances['hsa'], Decimal('0'))

    def test_get_account_balances_all_traditional_types(self):
        """Test that all traditional account types are categorized correctly."""
        user = User.objects.create_user(
            username='traditionaluser',
            email='traditional@example.com',
            password='testpass123'
        )
        portfolio = Portfolio.objects.create(user=user)

        # Create all traditional account types
        Account.objects.create(
            portfolio=portfolio,
            account_name='401k',
            account_type='trad_401k',
            current_value=Decimal('100000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Traditional IRA',
            account_type='trad_ira',
            current_value=Decimal('50000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='SEP IRA',
            account_type='sep_ira',
            current_value=Decimal('75000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Solo 401k',
            account_type='solo_401k',
            current_value=Decimal('60000.00'),
            status='active'
        )

        profile = TaxProfile.objects.create(user=user)
        balances = profile.get_account_balances_from_portfolio()

        self.assertEqual(balances['traditional'], Decimal('285000.00'))

    def test_get_account_balances_all_roth_types(self):
        """Test that all Roth account types are categorized correctly."""
        user = User.objects.create_user(
            username='rothuser',
            email='roth@example.com',
            password='testpass123'
        )
        portfolio = Portfolio.objects.create(user=user)

        # Create all Roth account types
        Account.objects.create(
            portfolio=portfolio,
            account_name='Roth 401k',
            account_type='roth_401k',
            current_value=Decimal('80000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Roth IRA',
            account_type='roth_ira',
            current_value=Decimal('120000.00'),
            status='active'
        )

        profile = TaxProfile.objects.create(user=user)
        balances = profile.get_account_balances_from_portfolio()

        self.assertEqual(balances['roth'], Decimal('200000.00'))

    def test_get_account_balances_all_taxable_types(self):
        """Test that all taxable account types are categorized correctly."""
        user = User.objects.create_user(
            username='taxableuser',
            email='taxable@example.com',
            password='testpass123'
        )
        portfolio = Portfolio.objects.create(user=user)

        # Create various taxable account types
        Account.objects.create(
            portfolio=portfolio,
            account_name='Taxable Brokerage',
            account_type='taxable_brokerage',
            current_value=Decimal('50000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='HYSA',
            account_type='hysa',
            current_value=Decimal('10000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Savings',
            account_type='savings',
            current_value=Decimal('15000.00'),
            status='active'
        )
        Account.objects.create(
            portfolio=portfolio,
            account_name='Money Market',
            account_type='money_market',
            current_value=Decimal('20000.00'),
            status='active'
        )

        profile = TaxProfile.objects.create(user=user)
        balances = profile.get_account_balances_from_portfolio()

        self.assertEqual(balances['taxable'], Decimal('95000.00'))

    def test_multiple_users_multiple_profiles(self):
        """Test multiple users can have different tax profiles."""
        user2 = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='testpass123'
        )
        profile2 = TaxProfile.objects.create(
            user=user2,
            filing_status='single',
            state_of_residence='TX'
        )
        self.assertNotEqual(self.tax_profile, profile2)
        self.assertEqual(self.tax_profile.user, self.user)
        self.assertEqual(profile2.user, user2)
