"""
Forms for financial app.
"""

from django import forms
from .models import FinancialProfile, Asset, IncomeSource, Expense, Portfolio, Account, AccountValueHistory


class FinancialProfileForm(forms.ModelForm):
    """Form for editing financial profile."""

    def __init__(self, *args, **kwargs):
        """Initialize form and preserve decimal formatting for age fields."""
        super().__init__(*args, **kwargs)
        # If we have an instance, explicitly format age fields with 1 decimal place
        if self.instance and self.instance.pk:
            if self.instance.current_age:
                self.initial['current_age'] = f"{self.instance.current_age:.1f}"
            if self.instance.retirement_age:
                self.initial['retirement_age'] = f"{self.instance.retirement_age:.1f}"

    class Meta:
        model = FinancialProfile
        fields = [
            'current_age',
            'retirement_age',
            'life_expectancy',
            'annual_spending',
            'social_security_annual',
            'pension_annual',
        ]
        widgets = {
            'current_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'number',
                'min': '18',
                'step': '0.1',
            }),
            'retirement_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'number',
                'min': '18',
                'step': '0.1',
            }),
            'life_expectancy': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '1',
                'step': '1',
            }),
            'annual_spending': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'step': '0.01',
            }),
            'social_security_annual': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'step': '0.01',
            }),
            'pension_annual': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'step': '0.01',
            }),
        }

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        current_age = cleaned_data.get('current_age')
        retirement_age = cleaned_data.get('retirement_age')
        life_expectancy = cleaned_data.get('life_expectancy')

        if current_age and retirement_age and current_age > retirement_age:
            raise forms.ValidationError('Retirement age must be greater than or equal to current age.')

        if retirement_age and life_expectancy and retirement_age >= life_expectancy:
            raise forms.ValidationError('Life expectancy must be greater than retirement age.')

        return cleaned_data


class AssetForm(forms.ModelForm):
    """Form for creating/editing assets."""

    class Meta:
        model = Asset
        fields = ['name', 'asset_type', 'current_value', 'annual_return_rate', 'allocation_percentage']


class IncomeSourceForm(forms.ModelForm):
    """Form for creating/editing income sources."""

    class Meta:
        model = IncomeSource
        fields = ['name', 'income_type', 'annual_amount', 'start_age', 'end_age', 'is_active']


class ExpenseForm(forms.ModelForm):
    """Form for creating/editing expenses."""

    class Meta:
        model = Expense
        fields = ['name', 'expense_type', 'amount', 'frequency', 'start_age', 'end_age', 'is_active']


class PortfolioForm(forms.ModelForm):
    """Form for creating and updating portfolios."""

    class Meta:
        model = Portfolio
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'My Portfolio'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'Portfolio description...',
                'rows': 3
            }),
        }


class AccountForm(forms.ModelForm):
    """Form for creating and updating accounts."""

    class Meta:
        model = Account
        fields = [
            'account_name', 'account_type', 'institution_name', 'account_number',
            'current_value', 'default_growth_rate', 'inflation_adjustment',
            'expected_contribution_rate', 'tax_treatment', 'status', 'description'
        ]
        widgets = {
            'account_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'My Savings Account'
            }),
            'account_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            }),
            'institution_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'Bank of America'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '****1234'
            }),
            'current_value': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'default_growth_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '7.0',
                'step': '0.1',
                'value': '7.0'
            }),
            'inflation_adjustment': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '0.0',
                'step': '0.1'
            }),
            'expected_contribution_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '0.0',
                'step': '0.1'
            }),
            'withdrawal_priority': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '0'
            }),
            'tax_treatment': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            }),
            'rmd_age': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'min': '59',
                'max': '100'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'Account description...',
                'rows': 3
            }),
        }


class AccountValueHistoryForm(forms.ModelForm):
    """Form for recording account values."""

    class Meta:
        model = AccountValueHistory
        fields = ['value', 'recorded_date', 'source', 'notes']
        widgets = {
            'value': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'recorded_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'type': 'date'
            }),
            'source': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'Notes about this value recording...',
                'rows': 3
            }),
        }
