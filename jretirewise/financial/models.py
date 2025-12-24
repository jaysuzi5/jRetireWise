"""
Financial data models for jRetireWise.
Includes Phase 1 assets, income, expenses and Phase 2 advanced portfolio management.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class FinancialProfile(models.Model):
    """User's financial profile with retirement planning parameters."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_profile')
    current_age = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(18)])
    retirement_age = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(18)])
    life_expectancy = models.IntegerField(validators=[MinValueValidator(1)], default=95)
    annual_spending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    social_security_annual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_annual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_start_age = models.IntegerField(validators=[MinValueValidator(18)], default=65, null=True, blank=True)
    current_portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_profile'
        verbose_name = 'Financial Profile'
        verbose_name_plural = 'Financial Profiles'

    def __str__(self):
        return f"Financial Profile of {self.user.email}"


class Asset(models.Model):
    """Asset owned by user (stock, bonds, cash, real estate, etc.)."""

    ASSET_TYPES = [
        ('cash', 'Cash'),
        ('stock', 'Stocks'),
        ('bond', 'Bonds'),
        ('real_estate', 'Real Estate'),
        ('retirement_account', 'Retirement Account'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    annual_return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.07,
        help_text='Expected annual return (e.g., 0.07 for 7%)'
    )
    allocation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Percentage of total portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['asset_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.asset_type})"


class IncomeSource(models.Model):
    """Income source for user (salary, Social Security, pension, etc.)."""

    INCOME_TYPES = [
        ('salary', 'Salary'),
        ('social_security', 'Social Security'),
        ('pension', 'Pension'),
        ('rental_income', 'Rental Income'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income_sources')
    name = models.CharField(max_length=255)
    income_type = models.CharField(max_length=50, choices=INCOME_TYPES)
    annual_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_age = models.IntegerField(validators=[MinValueValidator(18)], null=True, blank=True)
    end_age = models.IntegerField(validators=[MinValueValidator(18)], null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'income_source'
        verbose_name = 'Income Source'
        verbose_name_plural = 'Income Sources'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['income_type']),
        ]

    def __str__(self):
        return f"{self.name} (${self.annual_amount:,.2f}/year)"


class Expense(models.Model):
    """Expense category for user."""

    EXPENSE_TYPES = [
        ('housing', 'Housing'),
        ('utilities', 'Utilities'),
        ('food', 'Food'),
        ('transportation', 'Transportation'),
        ('healthcare', 'Healthcare'),
        ('insurance', 'Insurance'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]

    FREQUENCY_TYPES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('one_time', 'One Time'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    name = models.CharField(max_length=255)
    expense_type = models.CharField(max_length=50, choices=EXPENSE_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_TYPES, default='monthly')
    start_age = models.IntegerField(validators=[MinValueValidator(18)], null=True, blank=True)
    end_age = models.IntegerField(validators=[MinValueValidator(18)], null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expense'
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['expense_type']),
        ]

    def __str__(self):
        return f"{self.name} (${self.amount:,.2f}/{self.frequency})"

    def annual_amount(self):
        """Calculate annual amount based on frequency."""
        if self.frequency == 'monthly':
            return float(self.amount) * 12
        elif self.frequency == 'annual':
            return float(self.amount)
        else:
            return float(self.amount)


# ============================================================================
# Phase 2.0 - Advanced Portfolio Management Models
# ============================================================================


class Portfolio(models.Model):
    """User's investment portfolio container."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    name = models.CharField(max_length=255, default='My Portfolio')
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolio'
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'

    def __str__(self):
        return f"Portfolio: {self.name}"

    def get_total_value(self):
        """Calculate total portfolio value across all accounts."""
        return sum(
            account.current_value for account in self.accounts.filter(status='active')
        ) or Decimal('0.00')

    def get_accounts_by_type(self):
        """Group accounts by type with totals."""
        accounts_by_type = {}
        for account in self.accounts.filter(status='active'):
            account_type = account.get_account_type_display()
            if account_type not in accounts_by_type:
                accounts_by_type[account_type] = {
                    'accounts': [],
                    'total_value': Decimal('0.00')
                }
            accounts_by_type[account_type]['accounts'].append(account)
            accounts_by_type[account_type]['total_value'] += account.current_value

        return accounts_by_type


class Account(models.Model):
    """Individual investment account with detailed properties."""

    # Account type choices
    ACCOUNT_TYPES = [
        # Retirement Accounts
        ('trad_401k', 'Traditional 401(k)'),
        ('roth_401k', 'Roth 401(k)'),
        ('trad_ira', 'Traditional IRA'),
        ('roth_ira', 'Roth IRA'),
        ('sep_ira', 'SEP IRA'),
        ('solo_401k', 'Solo 401(k)'),

        # Investment Accounts
        ('taxable_brokerage', 'Taxable Brokerage'),
        ('joint_account', 'Joint Investment Account'),
        ('partnership', 'Partnership Account'),

        # Savings Accounts
        ('savings', 'Savings Account'),
        ('hysa', 'High-Yield Savings Account'),
        ('money_market', 'Money Market Account'),

        # Health-Related
        ('hsa', 'Health Savings Account'),
        ('msa', 'Medical Savings Account'),

        # Other
        ('529_plan', 'College 529 Plan'),
        ('certificate_cd', 'Certificate of Deposit'),
        ('bonds', 'Bonds'),
        ('treasuries', 'Treasury Securities'),
        ('custom', 'Custom Account Type'),
    ]

    # Tax treatment choices
    TAX_TREATMENT = [
        ('pre_tax', 'Pre-Tax'),
        ('post_tax', 'Post-Tax'),
        ('tax_exempt', 'Tax-Exempt'),
    ]

    # Account status choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('merged', 'Merged'),
    ]

    # Account-to-portfolio relationship
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='accounts')

    # Basic Information
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    account_name = models.CharField(max_length=255, help_text='User-friendly account name')
    account_number = models.CharField(max_length=50, blank=True, null=True, help_text='Account reference/number')
    institution_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Financial Data
    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    default_growth_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.07'),
        help_text='Annual % return (e.g., 0.07 for 7%)',
        validators=[MinValueValidator(Decimal('-1.00')), MaxValueValidator(Decimal('1.00'))]
    )
    inflation_adjustment = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.00'),
        help_text='Inflation adjustment applied to growth rate (0.03 = 3%)',
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))]
    )
    expected_contribution_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.00'),
        help_text='Expected annual contributions as % of current value'
    )

    # Investment Allocation (JSON: {stocks: %, bonds: %, other: %})
    investment_allocation = models.JSONField(
        default=dict,
        help_text='Investment allocation: {"stocks": 60, "bonds": 30, "other": 10}'
    )

    # Withdrawal Rules
    withdrawal_priority = models.IntegerField(
        default=0,
        help_text='Order to withdraw from this account (lower = first)'
    )
    withdrawal_restrictions = models.JSONField(
        default=dict,
        help_text='Withdrawal restrictions: {"min_age": 59.5, "penalty_free_date": "2030-01-01"}'
    )
    tax_treatment = models.CharField(max_length=20, choices=TAX_TREATMENT, default='pre_tax')

    # RMD (Required Minimum Distribution)
    rmd_age = models.IntegerField(
        default=72,
        help_text='Age at which RMD begins',
        validators=[MinValueValidator(50), MaxValueValidator(100)]
    )
    rmd_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.00'),
        help_text='RMD percentage (calculated as 1/life_expectancy_divisor)'
    )

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    data_source = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual Entry'),
            ('import', 'CSV Import'),
            ('api', 'API Sync'),
        ],
        default='manual'
    )

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        indexes = [
            models.Index(fields=['portfolio']),
            models.Index(fields=['account_type']),
            models.Index(fields=['status']),
            models.Index(fields=['withdrawal_priority']),
        ]
        ordering = ['withdrawal_priority', 'account_name']

    def __str__(self):
        return f"{self.account_name} ({self.get_account_type_display()})"

    def get_effective_growth_rate(self):
        """Calculate effective growth rate after inflation adjustment."""
        return self.default_growth_rate - self.inflation_adjustment

    def get_annual_contribution(self):
        """Calculate expected annual contribution in dollars."""
        return self.current_value * self.expected_contribution_rate

    def is_penalty_free_withdrawal_age(self, age):
        """Check if account allows penalty-free withdrawals at given age."""
        restrictions = self.withdrawal_restrictions or {}
        min_age = restrictions.get('min_age')
        if min_age:
            return age >= float(min_age)
        return False


class AccountValueHistory(models.Model):
    """Historical snapshots of account values over time."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='value_history')
    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    recorded_date = models.DateField(help_text='Date the value snapshot was recorded')
    recorded_timestamp = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='account_history_entries'
    )
    source = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual Entry'),
            ('import', 'CSV Import'),
            ('system', 'System Generated'),
        ],
        default='manual'
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'account_value_history'
        verbose_name = 'Account Value History'
        verbose_name_plural = 'Account Value History'
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['recorded_date']),
        ]
        ordering = ['-recorded_date']

    def __str__(self):
        return f"{self.account.account_name} - ${self.value:,.2f} on {self.recorded_date}"


class PortfolioSnapshot(models.Model):
    """Full portfolio snapshot at a point in time."""

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='snapshots')
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    snapshot_date = models.DateField(help_text='Date of the snapshot')
    created_timestamp = models.DateTimeField(auto_now_add=True)
    calculated_from = models.CharField(
        max_length=50,
        choices=[
            ('all_accounts', 'All Accounts'),
            ('last_snapshot', 'Last Snapshot'),
        ],
        default='all_accounts'
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'portfolio_snapshot'
        verbose_name = 'Portfolio Snapshot'
        verbose_name_plural = 'Portfolio Snapshots'
        indexes = [
            models.Index(fields=['portfolio']),
            models.Index(fields=['snapshot_date']),
        ]
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"Portfolio Snapshot - ${self.total_value:,.2f} on {self.snapshot_date}"


# ============================================================================
# Phase 2 - Tax Planning and Withdrawal Optimization Models
# ============================================================================


class TaxProfile(models.Model):
    """User's tax filing information for tax-aware calculations.

    Stores only tax-specific data (filing status and state).
    Other data is pulled from FinancialProfile and Portfolio models.
    """

    FILING_STATUS_CHOICES = [
        ('single', 'Single'),
        ('mfj', 'Married Filing Jointly'),
        ('mfs', 'Married Filing Separately'),
        ('hoh', 'Head of Household'),
        ('qw', 'Qualifying Widow(er)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tax_profile')

    # Tax Filing Information
    filing_status = models.CharField(
        max_length=10,
        choices=FILING_STATUS_CHOICES,
        default='single',
        help_text='Tax filing status for federal income tax calculations'
    )
    state_of_residence = models.CharField(
        max_length=50,
        default='',
        blank=True,
        help_text='State of residence for state income tax calculations'
    )

    # Social Security monthly benefits by claiming age
    social_security_age_62 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated monthly Social Security benefit if claimed at age 62 (~70% of FRA)'
    )
    social_security_age_65 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated monthly Social Security benefit if claimed at age 65 (~86% of FRA)'
    )
    social_security_age_67 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated monthly Social Security benefit if claimed at age 67 (100% - Full Retirement Age)'
    )
    social_security_age_70 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Estimated monthly Social Security benefit if claimed at age 70 (~124% of FRA with delayed credits)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tax_profile'
        verbose_name = 'Tax Profile'
        verbose_name_plural = 'Tax Profiles'

    def __str__(self):
        return f"Tax Profile for {self.user.email} ({self.get_filing_status_display()})"

    def get_account_balances_from_portfolio(self):
        """
        Get account balances grouped by tax treatment from user's portfolio.

        Returns:
            dict: Account balances by type:
                {
                    'traditional': Decimal,  # Pre-tax accounts (Traditional IRA, 401k)
                    'roth': Decimal,          # Roth accounts (Roth IRA, Roth 401k)
                    'taxable': Decimal,       # Taxable brokerage accounts
                    'hsa': Decimal,           # Health Savings Accounts
                }
        """
        balances = {
            'traditional': Decimal('0'),
            'roth': Decimal('0'),
            'taxable': Decimal('0'),
            'hsa': Decimal('0'),
        }

        # Define account type categories (account_type takes precedence over tax_treatment)
        TRADITIONAL_TYPES = ('trad_401k', 'trad_ira', 'sep_ira', 'solo_401k')
        ROTH_TYPES = ('roth_401k', 'roth_ira')
        HSA_TYPES = ('hsa', 'msa')
        TAXABLE_TYPES = (
            'taxable_brokerage', 'joint_account', 'partnership',  # Investment accounts
            'savings', 'hysa', 'money_market',  # Savings accounts (taxable interest)
            'certificate_cd', 'bonds', 'treasuries',  # Fixed income (taxable)
            '529_plan', 'custom'  # Other (default to taxable)
        )

        try:
            portfolio = self.user.portfolio
            for account in portfolio.accounts.filter(status='active'):
                account_type = account.account_type

                # Classify by account_type first (most reliable)
                if account_type in TRADITIONAL_TYPES:
                    balances['traditional'] += account.current_value
                elif account_type in ROTH_TYPES:
                    balances['roth'] += account.current_value
                elif account_type in HSA_TYPES:
                    balances['hsa'] += account.current_value
                elif account_type in TAXABLE_TYPES:
                    balances['taxable'] += account.current_value
                else:
                    # Unknown account type - default to taxable
                    balances['taxable'] += account.current_value

        except Exception:
            # If no portfolio exists, return zeros
            pass

        return balances
