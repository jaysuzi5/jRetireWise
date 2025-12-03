"""
Forms for financial app.
"""

from django import forms
from .models import FinancialProfile, Asset, IncomeSource, Expense


class FinancialProfileForm(forms.ModelForm):
    """Form for editing financial profile."""

    def __init__(self, *args, **kwargs):
        """Initialize form and preserve decimal formatting for age fields."""
        super().__init__(*args, **kwargs)
        # If we have an instance, explicitly format age fields with 2 decimal places
        if self.instance and self.instance.pk:
            if self.instance.current_age:
                self.initial['current_age'] = f"{self.instance.current_age:.2f}"
            if self.instance.retirement_age:
                self.initial['retirement_age'] = f"{self.instance.retirement_age:.2f}"

    class Meta:
        model = FinancialProfile
        fields = [
            'current_age',
            'retirement_age',
            'life_expectancy',
            'current_portfolio_value',
            'annual_spending',
            'social_security_annual',
            'pension_annual',
        ]
        widgets = {
            'current_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'number',
                'min': '18',
                'step': '0.01',
            }),
            'retirement_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'number',
                'min': '18',
                'step': '0.01',
            }),
            'life_expectancy': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '1',
                'step': '1',
            }),
            'current_portfolio_value': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'step': '0.01',
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
