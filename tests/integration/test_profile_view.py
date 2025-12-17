"""
Integration tests for ProfileView rendering with TaxProfileForm
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from jretirewise.financial.models import FinancialProfile, TaxProfile


class ProfileViewTestCase(TestCase):
    """Test ProfileView displays both forms correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create financial profile
        self.financial_profile = FinancialProfile.objects.create(
            user=self.user,
            current_age=Decimal('60'),
            retirement_age=Decimal('65'),
            life_expectancy=95,
            annual_spending=Decimal('80000'),
            social_security_annual=Decimal('44400'),
            pension_annual=Decimal('0'),
            current_portfolio_value=Decimal('1000000'),
        )

        # Create tax profile
        self.tax_profile = TaxProfile.objects.create(
            user=self.user,
            filing_status='mfj',
            full_retirement_age=67,
            social_security_age_62=Decimal('2500.00'),
            social_security_age_65=Decimal('3200.00'),
            social_security_age_67=Decimal('3700.00'),
            social_security_age_70=Decimal('4600.00'),
            traditional_ira_balance=Decimal('250000'),
            roth_ira_balance=Decimal('100000'),
            taxable_account_balance=Decimal('150000'),
        )

    def test_profile_page_shows_financial_form(self):
        """Test that profile page displays financial form."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('financial_profile', response.context)
        # Check form fields are rendered
        self.assertIn('current_age', str(response.content))
        self.assertIn('retirement_age', str(response.content))

    def test_profile_page_shows_tax_form(self):
        """Test that profile page displays tax form."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('tax_form', response.context)
        self.assertIn('tax_profile', response.context)
        # Check tax form fields are rendered
        self.assertIn('filing_status', str(response.content))
        self.assertIn('social_security_age_62', str(response.content))
        self.assertIn('social_security_age_70', str(response.content))

    def test_financial_form_submission(self):
        """Test submitting financial profile form."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/profile/', {
            'current_age': '62',
            'retirement_age': '65',
            'life_expectancy': '95',
            'annual_spending': '85000',
            'social_security_annual': '44400',
            'pension_annual': '0',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify financial profile was updated
        profile = FinancialProfile.objects.get(user=self.user)
        self.assertEqual(profile.annual_spending, Decimal('85000'))

    def test_tax_form_submission(self):
        """Test submitting tax profile form."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/profile/', {
            'filing_status': 'single',
            'state_of_residence': 'CA',
            'full_retirement_age': '67',
            'social_security_age_62': '2500.00',
            'social_security_age_65': '3200.00',
            'social_security_age_67': '3700.00',
            'social_security_age_70': '5000.00',
            'traditional_ira_balance': '250000',
            'roth_ira_balance': '100000',
            'taxable_account_balance': '150000',
            'hsa_balance': '0',
            'pension_annual': '0',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify tax profile was updated
        tax_profile = TaxProfile.objects.get(user=self.user)
        self.assertEqual(tax_profile.filing_status, 'single')
        self.assertEqual(tax_profile.state_of_residence, 'CA')
        self.assertEqual(tax_profile.social_security_age_70, Decimal('5000.00'))
