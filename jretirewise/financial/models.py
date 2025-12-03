"""
Financial data models for jRetireWise.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class FinancialProfile(models.Model):
    """User's financial profile with retirement planning parameters."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_profile')
    current_age = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(18)])
    retirement_age = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(18)])
    life_expectancy = models.IntegerField(validators=[MinValueValidator(1)], default=95)
    annual_spending = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    social_security_annual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_annual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
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
