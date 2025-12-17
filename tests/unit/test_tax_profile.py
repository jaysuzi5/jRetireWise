"""
Unit tests for TaxProfile model (Phase 0 - Social Security Profile Enhancement).
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from jretirewise.financial.models import TaxProfile


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
            state_of_residence='CA',
            full_retirement_age=67,
            social_security_age_62=Decimal('2500.00'),  # Monthly
            social_security_age_65=Decimal('3200.00'),
            social_security_age_67=Decimal('3700.00'),
            social_security_age_70=Decimal('4600.00'),
            traditional_ira_balance=Decimal('250000.00'),
            roth_ira_balance=Decimal('100000.00'),
            taxable_account_balance=Decimal('150000.00'),
            hsa_balance=Decimal('10000.00'),
            pension_annual=Decimal('30000.00'),
        )

    def test_tax_profile_creation(self):
        """Test TaxProfile can be created."""
        self.assertEqual(self.tax_profile.user, self.user)
        self.assertEqual(self.tax_profile.filing_status, 'mfj')
        self.assertEqual(self.tax_profile.state_of_residence, 'CA')

    def test_tax_profile_str_representation(self):
        """Test TaxProfile string representation."""
        self.assertIn(self.user.email, str(self.tax_profile))

    def test_social_security_fields_stored_as_monthly(self):
        """Test that Social Security fields are stored as monthly amounts."""
        self.assertEqual(self.tax_profile.social_security_age_62, Decimal('2500.00'))
        self.assertEqual(self.tax_profile.social_security_age_65, Decimal('3200.00'))
        self.assertEqual(self.tax_profile.social_security_age_67, Decimal('3700.00'))
        self.assertEqual(self.tax_profile.social_security_age_70, Decimal('4600.00'))

    def test_get_social_security_annual_age_62(self):
        """Test get_social_security_annual for age 62."""
        annual = self.tax_profile.get_social_security_annual(62)
        expected = Decimal('2500.00') * Decimal('12')
        self.assertEqual(annual, expected)
        self.assertEqual(annual, Decimal('30000.00'))

    def test_get_social_security_annual_age_65(self):
        """Test get_social_security_annual for age 65."""
        annual = self.tax_profile.get_social_security_annual(65)
        expected = Decimal('3200.00') * Decimal('12')
        self.assertEqual(annual, expected)
        self.assertEqual(annual, Decimal('38400.00'))

    def test_get_social_security_annual_age_67(self):
        """Test get_social_security_annual for age 67 (FRA)."""
        annual = self.tax_profile.get_social_security_annual(67)
        expected = Decimal('3700.00') * Decimal('12')
        self.assertEqual(annual, expected)
        self.assertEqual(annual, Decimal('44400.00'))

    def test_get_social_security_annual_age_70(self):
        """Test get_social_security_annual for age 70."""
        annual = self.tax_profile.get_social_security_annual(70)
        expected = Decimal('4600.00') * Decimal('12')
        self.assertEqual(annual, expected)
        self.assertEqual(annual, Decimal('55200.00'))

    def test_get_social_security_annual_invalid_age_raises_error(self):
        """Test get_social_security_annual raises error for invalid age."""
        with self.assertRaises(ValueError) as context:
            self.tax_profile.get_social_security_annual(60)
        self.assertIn('62, 65, 67, or 70', str(context.exception))

    def test_get_social_security_annual_invalid_age_63_raises_error(self):
        """Test get_social_security_annual raises error for age 63."""
        with self.assertRaises(ValueError):
            self.tax_profile.get_social_security_annual(63)

    def test_get_social_security_annual_invalid_age_71_raises_error(self):
        """Test get_social_security_annual raises error for age 71."""
        with self.assertRaises(ValueError):
            self.tax_profile.get_social_security_annual(71)

    def test_get_social_security_annual_returns_decimal(self):
        """Test get_social_security_annual returns Decimal type."""
        annual = self.tax_profile.get_social_security_annual(67)
        self.assertIsInstance(annual, Decimal)

    def test_get_social_security_annual_with_zero_benefit(self):
        """Test get_social_security_annual with zero benefit amount."""
        profile = TaxProfile.objects.create(
            user=User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='testpass123'
            ),
            social_security_age_67=Decimal('0.00'),
        )
        annual = profile.get_social_security_annual(67)
        self.assertEqual(annual, Decimal('0.00'))

    def test_account_balances_default_to_zero(self):
        """Test that account balances default to zero."""
        new_user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        profile = TaxProfile.objects.create(user=new_user)
        self.assertEqual(profile.traditional_ira_balance, Decimal('0.00'))
        self.assertEqual(profile.roth_ira_balance, Decimal('0.00'))
        self.assertEqual(profile.taxable_account_balance, Decimal('0.00'))
        self.assertEqual(profile.hsa_balance, Decimal('0.00'))

    def test_filing_status_choices(self):
        """Test filing status choices are correct."""
        valid_statuses = ['single', 'mfj', 'mfs', 'hoh', 'qw']
        for status in valid_statuses:
            profile = TaxProfile.objects.create(
                user=User.objects.create_user(
                    username=f'user_{status}',
                    email=f'{status}@example.com',
                    password='testpass123'
                ),
                filing_status=status
            )
            self.assertEqual(profile.filing_status, status)

    def test_full_retirement_age_default(self):
        """Test full retirement age defaults to 67."""
        new_user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        profile = TaxProfile.objects.create(user=new_user)
        self.assertEqual(profile.full_retirement_age, 67)

    def test_onetoone_relationship_with_user(self):
        """Test TaxProfile has OneToOne relationship with User."""
        # User should only have one tax profile
        self.assertEqual(self.user.tax_profile, self.tax_profile)
        # Creating another tax profile for same user should fail
        with self.assertRaises(Exception):
            TaxProfile.objects.create(user=self.user)

    def test_pension_and_account_balances(self):
        """Test pension and account balances are stored correctly."""
        self.assertEqual(self.tax_profile.pension_annual, Decimal('30000.00'))
        self.assertEqual(self.tax_profile.traditional_ira_balance, Decimal('250000.00'))
        self.assertEqual(self.tax_profile.roth_ira_balance, Decimal('100000.00'))
        self.assertEqual(self.tax_profile.taxable_account_balance, Decimal('150000.00'))
        self.assertEqual(self.tax_profile.hsa_balance, Decimal('10000.00'))

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
            state_of_residence='TX',
            social_security_age_67=Decimal('5000.00'),
        )
        self.assertNotEqual(self.tax_profile, profile2)
        self.assertEqual(self.tax_profile.user, self.user)
        self.assertEqual(profile2.user, user2)
