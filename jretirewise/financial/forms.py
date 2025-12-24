"""
Forms for financial app.
"""

from django import forms
from decimal import Decimal
from .models import FinancialProfile, Asset, IncomeSource, Expense, Portfolio, Account, AccountValueHistory, TaxProfile


class PercentageNumberInput(forms.NumberInput):
    """Custom widget that converts decimals (0.07) to percentages (7.0) for display."""

    def prepare_value(self, value):
        """Convert decimal to percentage for display in HTML form."""
        if value is None or value == '':
            return value
        try:
            # Convert decimal (0.07) to percentage (7.0)
            numeric_value = float(value)
            if 0 <= numeric_value <= 1:  # Assume it's a decimal if between 0 and 1
                return numeric_value * 100
            return numeric_value
        except (ValueError, TypeError):
            return value


class FinancialProfileForm(forms.ModelForm):
    """Combined form for editing financial and tax profile.

    Account balances are managed in the Portfolio section.
    Social Security is entered as annual amount in this form.
    Tax filing status and state are stored in TaxProfile.
    """

    # Tax profile fields (only filing-specific data)
    filing_status = forms.ChoiceField(
        choices=TaxProfile.FILING_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
        })
    )
    state_of_residence = forms.CharField(
        required=False,
        max_length=2,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'CA',
            'maxlength': '2',
        })
    )

    # Social Security monthly benefits by claiming age
    social_security_age_62 = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    social_security_age_65 = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    social_security_age_67 = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )
    social_security_age_70 = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '0.00',
            'step': '0.01',
        })
    )

    def __init__(self, *args, **kwargs):
        """Initialize form and preserve decimal formatting for age fields."""
        super().__init__(*args, **kwargs)
        # If we have an instance, explicitly format age fields with 1 decimal place
        if self.instance and self.instance.pk:
            if self.instance.current_age:
                self.initial['current_age'] = f"{self.instance.current_age:.1f}"
            if self.instance.retirement_age:
                self.initial['retirement_age'] = f"{self.instance.retirement_age:.1f}"

        # Populate tax profile fields if instance has related tax profile
        if self.instance and self.instance.pk:
            try:
                tax_profile = self.instance.user.tax_profile
                self.initial['filing_status'] = tax_profile.filing_status
                self.initial['state_of_residence'] = tax_profile.state_of_residence
                self.initial['social_security_age_62'] = tax_profile.social_security_age_62
                self.initial['social_security_age_65'] = tax_profile.social_security_age_65
                self.initial['social_security_age_67'] = tax_profile.social_security_age_67
                self.initial['social_security_age_70'] = tax_profile.social_security_age_70
            except TaxProfile.DoesNotExist:
                pass

    class Meta:
        model = FinancialProfile
        fields = [
            'current_age',
            'retirement_age',
            'life_expectancy',
            'annual_spending',
            'social_security_annual',
            'pension_annual',
            'pension_start_age',
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
            'pension_start_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'number',
                'min': '18',
                'step': '1',
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


class TaxProfileForm(forms.ModelForm):
    """Form for editing tax filing information (status and state).

    Other data is now sourced from FinancialProfile and Portfolio models.
    """

    class Meta:
        model = TaxProfile
        fields = [
            'filing_status',
            'state_of_residence',
        ]
        widgets = {
            'filing_status': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'state_of_residence': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'CA',
                'maxlength': '2',
            }),
        }
        labels = {
            'filing_status': 'Tax Filing Status',
            'state_of_residence': 'State of Residence',
        }


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


class PercentageDecimalField(forms.DecimalField):
    """Custom DecimalField for percentage inputs that converts to/from percentage format."""

    def to_python(self, value):
        """Convert percentage input (6.0) to decimal (0.06)."""
        if value is None or value == '':
            return value
        try:
            # Get the raw value first
            numeric_value = float(value)
            # If it's in percentage format (0-100 range), convert to decimal
            if numeric_value > 1:
                numeric_value = numeric_value / 100
            return Decimal(str(numeric_value))
        except (ValueError, TypeError):
            return value

    def clean(self, value):
        """Validate after conversion to decimal."""
        if value is None or value == '':
            return value
        try:
            # Convert percentage to decimal if needed
            if isinstance(value, str):
                numeric_value = float(value)
                if numeric_value > 1:
                    numeric_value = numeric_value / 100
                value = Decimal(str(numeric_value))
            # Run parent validation on the decimal value
            return super().clean(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Enter a valid decimal number.')


class AccountForm(forms.ModelForm):
    """Form for creating and updating accounts."""

    # Override percentage fields with custom field class
    default_growth_rate = PercentageDecimalField(
        required=False,
        widget=PercentageNumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
            'placeholder': '7.0',
            'step': '0.1'
        }),
        help_text='Expected annual return as percentage (e.g., 7.0 for 7%)'
    )
    inflation_adjustment = PercentageDecimalField(
        required=False,
        widget=PercentageNumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
            'placeholder': '0.0',
            'step': '0.1'
        }),
        help_text='Inflation adjustment as percentage (e.g., 3.0 for 3%)'
    )
    expected_contribution_rate = PercentageDecimalField(
        required=False,
        widget=PercentageNumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
            'placeholder': '0.0',
            'step': '0.1'
        }),
        help_text='Expected contributions as percentage (e.g., 5.0 for 5%)'
    )

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

    def __init__(self, *args, **kwargs):
        """Initialize form and convert decimal growth rates to percentages for display."""
        super().__init__(*args, **kwargs)

        # Convert decimal growth rates (0.07) to percentages (7.0) for display
        # Must set self.initial dict for ModelForm rendering to pick up the converted values
        # Use Decimal math to avoid floating point imprecision
        if self.instance and self.instance.pk:
            # Editing existing account - convert decimal values to percentages for display
            if self.instance.default_growth_rate is not None:
                self.initial['default_growth_rate'] = float(Decimal(str(self.instance.default_growth_rate)) * Decimal('100'))
            if self.instance.inflation_adjustment is not None:
                self.initial['inflation_adjustment'] = float(Decimal(str(self.instance.inflation_adjustment)) * Decimal('100'))
            if self.instance.expected_contribution_rate is not None:
                self.initial['expected_contribution_rate'] = float(Decimal(str(self.instance.expected_contribution_rate)) * Decimal('100'))
        else:
            # Creating new account - set defaults
            self.initial['default_growth_rate'] = 7.0
            self.initial['inflation_adjustment'] = 0.0
            self.initial['expected_contribution_rate'] = 0.0

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        # PercentageDecimalField already converts percentages to decimals in to_python()
        # No additional conversion needed here
        return cleaned_data


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
