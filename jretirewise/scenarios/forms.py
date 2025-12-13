"""
Forms for scenarios app.
"""

from django import forms
from decimal import Decimal
import json
from .models import RetirementScenario, WithdrawalBucket


class ScenarioForm(forms.ModelForm):
    """Form for creating/editing retirement scenarios."""

    parameters_json = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm',
            'placeholder': '{"annual_return": 0.07, "inflation_rate": 0.03}',
        }),
        required=False,
        label='Parameters (JSON)',
        help_text='Optional. Provide JSON to override default parameters.'
    )

    class Meta:
        model = RetirementScenario
        fields = ['name', 'description', 'calculator_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'calculator_type': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate parameters_json from instance if available
        if self.instance and self.instance.pk:
            if isinstance(self.instance.parameters, dict):
                self.fields['parameters_json'].initial = json.dumps(self.instance.parameters, indent=2)
            elif isinstance(self.instance.parameters, str):
                self.fields['parameters_json'].initial = self.instance.parameters

    def clean_parameters_json(self):
        """Validate JSON parameters."""
        params_str = self.cleaned_data.get('parameters_json', '')
        if not params_str:
            return {}

        try:
            return json.loads(params_str)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Invalid JSON: {str(e)}')

    def save(self, commit=True):
        """Save scenario with parsed JSON parameters."""
        instance = super().save(commit=False)
        # Get the parsed parameters from clean_parameters_json
        instance.parameters = self.cleaned_data.get('parameters_json', {})
        if commit:
            instance.save()
        return instance


class MonteCarloScenarioForm(forms.ModelForm):
    """
    Enhanced form for Monte Carlo scenarios with proper field-level inputs.
    Pre-fills from FinancialProfile and Portfolio.
    """

    # Mode Selection
    calculation_mode = forms.ChoiceField(
        choices=[
            ('find_withdrawal', 'Find Safe Withdrawal for Target Success Rate'),
            ('evaluate_success', 'Evaluate Success Rate for Fixed Withdrawal'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio text-indigo-600',
        }),
        initial='find_withdrawal',
        label='Calculation Mode',
    )

    # Age Parameters
    retirement_age = forms.IntegerField(
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '65',
        }),
        label='Retirement Age',
    )

    life_expectancy = forms.IntegerField(
        min_value=50,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '95',
        }),
        label='Life Expectancy',
    )

    # Portfolio Parameters
    portfolio_value = forms.DecimalField(
        min_value=0,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '1,000,000',
            'step': '1000',
        }),
        label='Portfolio Balance ($)',
    )

    # Market Parameters (as percentages for user input)
    expected_return = forms.DecimalField(
        min_value=0,
        max_value=30,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '7.0',
            'step': '0.1',
        }),
        label='Expected Annual Return (%)',
        help_text='Historical stock market average is ~7%',
        initial=7.0,
    )

    inflation_rate = forms.DecimalField(
        min_value=0,
        max_value=20,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '3.0',
            'step': '0.1',
        }),
        label='Inflation Rate (%)',
        initial=3.0,
    )

    volatility = forms.DecimalField(
        min_value=0,
        max_value=50,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '15.0',
            'step': '0.5',
        }),
        label='Market Volatility / Std Dev (%)',
        help_text='Historical stock market volatility is ~15%',
        initial=15.0,
    )

    # Simulation Parameters
    num_simulations = forms.IntegerField(
        min_value=100,
        max_value=10000,
        initial=1000,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'step': '100',
        }),
        label='Number of Simulations',
    )

    # Mode-specific: Find Withdrawal
    target_success_rate = forms.IntegerField(
        min_value=50,
        max_value=99,
        initial=90,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '90',
        }),
        label='Target Success Rate (%)',
        help_text='The success rate you want to achieve (e.g., 90%)',
    )

    # Mode-specific: Evaluate Success
    withdrawal_amount = forms.DecimalField(
        min_value=0,
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '40,000',
        }),
        label='Withdrawal Amount ($)',
    )

    withdrawal_frequency = forms.ChoiceField(
        choices=[
            ('annual', 'Annual'),
            ('monthly', 'Monthly'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio text-indigo-600',
        }),
        initial='annual',
        label='Withdrawal Frequency',
    )

    # Social Security
    social_security_start_age = forms.IntegerField(
        min_value=62,
        max_value=70,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '67',
        }),
        label='Social Security Start Age',
        help_text='Age 62-70; leave blank to exclude',
    )

    social_security_monthly = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '2,500',
        }),
        label='Social Security Monthly Benefit ($)',
    )

    class Meta:
        model = RetirementScenario
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'My Monte Carlo Scenario',
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Optional description...',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Initialize with pre-filled values from user's profile and portfolio."""
        super().__init__(*args, **kwargs)
        self.user = user
        self._prefilled_fields = set()

        if user:
            self._prefill_from_profile(user)
            self._prefill_from_portfolio(user)

    def _prefill_from_profile(self, user):
        """Pre-fill form fields from user's FinancialProfile."""
        try:
            profile = user.financial_profile
            if profile.retirement_age:
                # Convert to integer for the form
                self.fields['retirement_age'].initial = int(profile.retirement_age)
                self._prefilled_fields.add('retirement_age')
            if profile.life_expectancy:
                self.fields['life_expectancy'].initial = int(profile.life_expectancy)
                self._prefilled_fields.add('life_expectancy')
            # Pre-fill SS if available (convert annual to monthly, round to 2 decimals)
            if profile.social_security_annual and profile.social_security_annual > 0:
                self.fields['social_security_monthly'].initial = round(float(profile.social_security_annual) / 12, 2)
                self._prefilled_fields.add('social_security_monthly')
        except Exception:
            pass  # Profile doesn't exist or error accessing

    def _prefill_from_portfolio(self, user):
        """Pre-fill form fields from user's Portfolio."""
        try:
            portfolio = user.portfolio
            total_value = portfolio.get_total_value()
            if total_value and total_value > 0:
                self.fields['portfolio_value'].initial = round(float(total_value), 2)
                self._prefilled_fields.add('portfolio_value')

                # Calculate weighted average return from accounts
                accounts = portfolio.accounts.filter(status='active')
                if accounts.exists():
                    total = float(total_value)
                    weighted_return = sum(
                        float(acc.default_growth_rate) * (float(acc.current_value) / total)
                        for acc in accounts if acc.current_value and acc.current_value > 0
                    )
                    if weighted_return > 0:
                        # default_growth_rate is stored as decimal (0.06 for 6%)
                        # Convert to percentage for display (6.0 for 6%)
                        self.fields['expected_return'].initial = round(weighted_return * 100, 1)
                        self._prefilled_fields.add('expected_return')
        except Exception:
            pass  # Portfolio doesn't exist or error accessing

    def get_prefilled_fields(self):
        """Return set of field names that were pre-filled from user data."""
        return self._prefilled_fields

    def clean(self):
        """Validate form and build parameters dict."""
        cleaned_data = super().clean()
        mode = cleaned_data.get('calculation_mode')

        # Validate mode-specific required fields
        if mode == 'find_withdrawal':
            if not cleaned_data.get('target_success_rate'):
                self.add_error('target_success_rate', 'Required for Find Withdrawal mode')
        else:  # evaluate_success
            if not cleaned_data.get('withdrawal_amount'):
                self.add_error('withdrawal_amount', 'Required for Evaluate Success mode')

        # Validate age relationships
        retirement_age = cleaned_data.get('retirement_age')
        life_expectancy = cleaned_data.get('life_expectancy')
        if retirement_age and life_expectancy and retirement_age >= life_expectancy:
            self.add_error('life_expectancy', 'Life expectancy must be greater than retirement age')

        # Convert monthly withdrawal to annual if needed
        if cleaned_data.get('withdrawal_frequency') == 'monthly' and cleaned_data.get('withdrawal_amount'):
            cleaned_data['withdrawal_amount_annual'] = float(cleaned_data['withdrawal_amount']) * 12
        else:
            cleaned_data['withdrawal_amount_annual'] = float(cleaned_data.get('withdrawal_amount') or 0)

        return cleaned_data

    def save(self, commit=True):
        """Save scenario with structured parameters."""
        instance = super().save(commit=False)
        instance.calculator_type = 'monte_carlo'

        # Build parameters JSON - convert percentages to decimals for calculator
        instance.parameters = {
            'mode': self.cleaned_data['calculation_mode'],
            'retirement_age': int(self.cleaned_data['retirement_age']),
            'life_expectancy': self.cleaned_data['life_expectancy'],
            'portfolio_value': float(self.cleaned_data['portfolio_value']),
            # Convert percentages to decimals
            'annual_return_rate': float(self.cleaned_data['expected_return']) / 100,
            'inflation_rate': float(self.cleaned_data['inflation_rate']) / 100,
            'return_std_dev': float(self.cleaned_data['volatility']) / 100,
            'num_simulations': self.cleaned_data['num_simulations'],
            'withdrawal_frequency': self.cleaned_data['withdrawal_frequency'],
            # Mode-specific
            'target_success_rate': float(self.cleaned_data.get('target_success_rate') or 90),
            'withdrawal_amount': self.cleaned_data.get('withdrawal_amount_annual', 0),
            # Social Security
            'social_security_start_age': self.cleaned_data.get('social_security_start_age'),
            'social_security_monthly': float(self.cleaned_data.get('social_security_monthly') or 0),
        }

        if self.user:
            instance.user = self.user

        if commit:
            instance.save()
        return instance


class BucketedWithdrawalScenarioForm(forms.ModelForm):
    """
    Form for creating/editing bucketed withdrawal scenarios.
    Pre-fills from FinancialProfile and Portfolio.
    """

    # Age Parameters
    retirement_age = forms.IntegerField(
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '65',
        }),
        label='Retirement Age',
    )

    life_expectancy = forms.IntegerField(
        min_value=50,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '95',
        }),
        label='Life Expectancy',
    )

    # Portfolio Parameters
    portfolio_value = forms.DecimalField(
        min_value=0,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '1,000,000',
            'step': '1000',
        }),
        label='Portfolio Balance ($)',
    )

    # Market Parameters (as percentages for user input)
    expected_return = forms.DecimalField(
        min_value=0,
        max_value=30,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '7.0',
            'step': '0.1',
        }),
        label='Expected Annual Return (%)',
        help_text='Historical stock market average is ~7%',
        initial=7.0,
    )

    inflation_rate = forms.DecimalField(
        min_value=0,
        max_value=20,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': '3.0',
            'step': '0.1',
        }),
        label='Inflation Rate (%)',
        initial=3.0,
    )

    class Meta:
        model = RetirementScenario
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'My Bucketed Withdrawal Strategy',
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Optional description...',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Initialize with pre-filled values from user's profile and portfolio."""
        super().__init__(*args, **kwargs)
        self.user = user
        self._prefilled_fields = set()

        if user:
            self._prefill_from_profile(user)
            self._prefill_from_portfolio(user)

    def _prefill_from_profile(self, user):
        """Pre-fill form fields from user's FinancialProfile."""
        try:
            profile = user.financial_profile
            if profile.retirement_age:
                self.fields['retirement_age'].initial = int(profile.retirement_age)
                self._prefilled_fields.add('retirement_age')
            if profile.life_expectancy:
                self.fields['life_expectancy'].initial = int(profile.life_expectancy)
                self._prefilled_fields.add('life_expectancy')
        except Exception:
            pass  # Profile doesn't exist or error accessing

    def _prefill_from_portfolio(self, user):
        """Pre-fill form fields from user's Portfolio."""
        try:
            portfolio = user.portfolio
            total_value = portfolio.get_total_value()
            if total_value and total_value > 0:
                self.fields['portfolio_value'].initial = round(float(total_value), 2)
                self._prefilled_fields.add('portfolio_value')

                # Calculate weighted average return from accounts
                accounts = portfolio.accounts.filter(status='active')
                if accounts.exists():
                    total = float(total_value)
                    weighted_return = sum(
                        float(acc.default_growth_rate) * (float(acc.current_value) / total)
                        for acc in accounts if acc.current_value and acc.current_value > 0
                    )
                    if weighted_return > 0:
                        # default_growth_rate is stored as decimal (0.06 for 6%)
                        # Convert to percentage for display (6.0 for 6%)
                        self.fields['expected_return'].initial = round(weighted_return * 100, 1)
                        self._prefilled_fields.add('expected_return')
        except Exception:
            pass  # Portfolio doesn't exist or error accessing

    def get_prefilled_fields(self):
        """Return set of field names that were pre-filled from user data."""
        return self._prefilled_fields

    def clean(self):
        """Validate form."""
        cleaned_data = super().clean()

        # Validate age relationships
        retirement_age = cleaned_data.get('retirement_age')
        life_expectancy = cleaned_data.get('life_expectancy')
        if retirement_age and life_expectancy and retirement_age >= life_expectancy:
            self.add_error('life_expectancy', 'Life expectancy must be greater than retirement age')

        return cleaned_data

    def save(self, commit=True):
        """Save scenario with structured parameters."""
        instance = super().save(commit=False)
        instance.calculator_type = 'bucketed_withdrawal'

        # Build parameters JSON - convert percentages to decimals for calculator
        instance.parameters = {
            'retirement_age': int(self.cleaned_data['retirement_age']),
            'life_expectancy': int(self.cleaned_data['life_expectancy']),
            'portfolio_value': float(self.cleaned_data['portfolio_value']),
            # Convert percentages to decimals
            'annual_return_rate': float(self.cleaned_data['expected_return']) / 100,
            'inflation_rate': float(self.cleaned_data['inflation_rate']) / 100,
        }

        if self.user:
            instance.user = self.user

        if commit:
            instance.save()
        return instance


class WithdrawalBucketForm(forms.ModelForm):
    """
    Form for creating/editing withdrawal buckets.
    """

    class Meta:
        model = WithdrawalBucket
        fields = [
            'bucket_name',
            'description',
            'order',
            'start_age',
            'end_age',
            'target_withdrawal_rate',
            'min_withdrawal_amount',
            'max_withdrawal_amount',
            'manual_withdrawal_override',
            'expected_pension_income',
            'expected_social_security_income',
            'healthcare_cost_adjustment',
            'tax_loss_harvesting_enabled',
            'roth_conversion_enabled',
        ]
        widgets = {
            'bucket_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'e.g., Early Retirement',
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Optional description of this bucket',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
            }),
            'start_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'min': '18',
                'max': '120',
                'placeholder': '55',
            }),
            'end_age': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'min': '18',
                'max': '120',
                'placeholder': '65',
            }),
            'target_withdrawal_rate': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'min': '0',
                'max': '20',
                'step': '0.1',
                'placeholder': '4.0',
            }),
            'min_withdrawal_amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'max_withdrawal_amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'manual_withdrawal_override': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'expected_pension_income': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'expected_social_security_income': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'healthcare_cost_adjustment': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '0',
                'step': '1000',
            }),
            'tax_loss_harvesting_enabled': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500',
            }),
            'roth_conversion_enabled': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500',
            }),
        }

    def clean(self):
        """Validate form."""
        cleaned_data = super().clean()

        # Validate age relationships
        start_age = cleaned_data.get('start_age')
        end_age = cleaned_data.get('end_age')

        if start_age and end_age:
            if start_age >= end_age:
                self.add_error('end_age', 'End age must be greater than start age')

        # Validate withdrawal rate
        rate = cleaned_data.get('target_withdrawal_rate')
        if rate is not None:
            if rate < 0 or rate > 20:
                self.add_error('target_withdrawal_rate', 'Withdrawal rate must be between 0 and 20%')

        # Validate min/max amounts
        min_amt = cleaned_data.get('min_withdrawal_amount')
        max_amt = cleaned_data.get('max_withdrawal_amount')

        if min_amt and max_amt and min_amt > 0 and max_amt > 0:
            if min_amt > max_amt:
                self.add_error('max_withdrawal_amount', 'Maximum amount must be greater than minimum')

        return cleaned_data
