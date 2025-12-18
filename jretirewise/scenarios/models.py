"""
Scenario and calculation result models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class RetirementScenario(models.Model):
    """A retirement scenario with specific parameters."""

    CALCULATOR_TYPES = [
        ('4_percent', '4% Rule'),
        ('4_7_percent', '4.7% Rule'),
        ('bucketed_withdrawal', 'Bucketed Withdrawal'),
        ('monte_carlo', 'Monte Carlo'),
        ('historical', 'Historical Analysis'),
    ]

    CLAIMING_AGE_CHOICES = [
        (62, '62 (Reduced benefit)'),
        (65, '65 (Partial benefit)'),
        (67, '67 (Full Retirement Age)'),
        (70, '70 (Delayed benefit)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    calculator_type = models.CharField(max_length=50, choices=CALCULATOR_TYPES)

    # Scenario parameters stored as JSON
    parameters = models.JSONField(default=dict)

    # Social Security claiming age (Phase 0 enhancement)
    social_security_claiming_age = models.IntegerField(
        default=67,
        choices=CLAIMING_AGE_CHOICES,
        help_text='Age at which user will claim Social Security'
    )

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scenario'
        verbose_name = 'Retirement Scenario'
        verbose_name_plural = 'Retirement Scenarios'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['calculator_type']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.calculator_type})"


class CalculationResult(models.Model):
    """Results from a calculation."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    scenario = models.OneToOneField(
        RetirementScenario,
        on_delete=models.CASCADE,
        related_name='result'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Result data as JSON
    result_data = models.JSONField(default=dict)

    # Execution metrics
    execution_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calculation_result'
        verbose_name = 'Calculation Result'
        verbose_name_plural = 'Calculation Results'
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Result for {self.scenario.name} ({self.status})"


class WithdrawalBucket(models.Model):
    """
    A withdrawal bucket for dynamic bucketed withdrawal rate calculations.

    Each bucket represents a time period (age range) with specific withdrawal
    parameters, account constraints, and special considerations.
    """

    scenario = models.ForeignKey(
        RetirementScenario,
        on_delete=models.CASCADE,
        related_name='withdrawal_buckets'
    )

    # Basic properties
    bucket_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    # Time period (age range OR year range)
    start_age = models.IntegerField(null=True, blank=True)
    end_age = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)

    # Withdrawal parameters
    target_withdrawal_rate = models.FloatField(help_text="Percentage of portfolio (e.g., 4.0 for 4%)")
    min_withdrawal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum withdrawal amount in dollars"
    )
    max_withdrawal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum withdrawal amount in dollars"
    )
    manual_withdrawal_override = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed withdrawal amount if set (overrides rate calculation)"
    )

    # Account constraints
    allowed_account_types = models.JSONField(
        default=list,
        help_text="List of allowed account type codes (e.g., ['traditional_401k', 'roth_ira'])"
    )
    prohibited_account_types = models.JSONField(
        default=list,
        help_text="List of prohibited account type codes"
    )
    withdrawal_order = models.JSONField(
        default=list,
        help_text="Ordered list of account IDs for withdrawal preference"
    )

    # Special considerations
    tax_loss_harvesting_enabled = models.BooleanField(default=False)
    roth_conversion_enabled = models.BooleanField(default=False)
    healthcare_cost_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Healthcare cost adjustment in dollars (positive increases withdrawal need)"
    )
    expected_pension_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Expected pension income per year (reduces portfolio withdrawal need)"
    )
    expected_social_security_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Expected Social Security income per year (reduces portfolio withdrawal need)"
    )

    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'withdrawal_bucket'
        verbose_name = 'Withdrawal Bucket'
        verbose_name_plural = 'Withdrawal Buckets'
        ordering = ['order', 'start_age']
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.bucket_name} ({self.scenario.name})"

    def get_age_range_display(self):
        """Return human-readable age range."""
        if self.start_age and self.end_age:
            return f"Age {self.start_age}-{self.end_age}"
        elif self.start_age:
            return f"Age {self.start_age}+"
        return "Unspecified"


class BucketedWithdrawalResult(models.Model):
    """
    Results from a single year of bucketed withdrawal calculation.

    These records are created by the DynamicBucketedWithdrawalCalculator
    and stored for analysis and visualization.
    """

    calculation = models.ForeignKey(
        CalculationResult,
        on_delete=models.CASCADE,
        related_name='bucketed_results'
    )
    bucket = models.ForeignKey(
        WithdrawalBucket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='results'
    )

    # Year information
    year = models.IntegerField()
    age = models.IntegerField(null=True, blank=True)

    # Withdrawal details
    target_rate = models.FloatField(help_text="Target withdrawal rate for this year (%)")
    calculated_withdrawal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Calculated withdrawal based on rate and portfolio value"
    )
    actual_withdrawal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Actual withdrawal amount (may differ due to constraints)"
    )
    withdrawal_accounts = models.JSONField(
        default=dict,
        help_text="Account-by-account withdrawal breakdown: {account_id: amount}"
    )

    # Portfolio tracking
    portfolio_value_start = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Portfolio value at start of year"
    )
    investment_growth = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Investment growth/returns during year"
    )
    portfolio_value_end = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Portfolio value at end of year after withdrawal"
    )

    # Additional income sources
    pension_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Pension income during year"
    )
    social_security_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Social Security income during year"
    )
    total_available_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total available income (withdrawal + pension + SS)"
    )

    # Notes and flags
    notes = models.TextField(
        blank=True,
        help_text="Notes about this year (RMD applied, early access penalty, etc.)"
    )
    flags = models.JSONField(
        default=list,
        help_text="Array of warning flags: ['rmd_applied', 'early_access_penalty', etc.]"
    )

    class Meta:
        db_table = 'bucketed_withdrawal_result'
        verbose_name = 'Bucketed Withdrawal Result'
        verbose_name_plural = 'Bucketed Withdrawal Results'
        unique_together = [['calculation', 'year']]
        ordering = ['calculation', 'year']
        indexes = [
            models.Index(fields=['calculation', 'year']),
            models.Index(fields=['bucket']),
        ]

    def __str__(self):
        return f"Year {self.year}, Age {self.age} - ${self.actual_withdrawal:,.2f} withdrawal"


class SensitivityAnalysis(models.Model):
    """Stores a sensitivity analysis for an existing scenario."""

    scenario = models.ForeignKey(
        RetirementScenario,
        on_delete=models.CASCADE,
        related_name='sensitivity_analyses'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Baseline adjustments (what was tested)
    return_adjustment = models.FloatField(
        default=0.0,
        help_text="Adjustment to return rate (e.g., -0.02 for -2%)"
    )
    spending_adjustment = models.FloatField(
        default=0.0,
        help_text="Adjustment to spending (e.g., 0.20 for +20%)"
    )
    inflation_adjustment = models.FloatField(
        default=0.0,
        help_text="Adjustment to inflation rate (e.g., 0.01 for +1%)"
    )

    # Parameter ranges tested (for tornado chart generation)
    return_range_min = models.FloatField(default=-0.05)  # -5%
    return_range_max = models.FloatField(default=0.05)   # +5%
    return_step = models.FloatField(default=0.01)        # 1% steps

    spending_range_min = models.FloatField(default=0.0)  # 0%
    spending_range_max = models.FloatField(default=0.50) # +50%
    spending_step = models.FloatField(default=0.10)      # 10% steps

    inflation_range_min = models.FloatField(default=0.0) # 0%
    inflation_range_max = models.FloatField(default=0.04)# +4%
    inflation_step = models.FloatField(default=0.01)     # 1% steps

    # Calculation results stored as JSON
    # Structure: {
    #   'success_rate': float,
    #   'final_value': float,
    #   'years_to_depletion': int|null,
    #   'comparison_to_baseline': {...},
    #   'tornado_data': [...],
    #   'portfolio_comparison': [...]
    # }
    result_data = models.JSONField(default=dict)

    # Execution metrics
    execution_time_ms = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sensitivity_analysis'
        verbose_name = 'Sensitivity Analysis'
        verbose_name_plural = 'Sensitivity Analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Sensitivity: {self.name} (on {self.scenario.name})"
