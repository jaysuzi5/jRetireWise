"""
Serializers for scenario and calculation models.
"""

from rest_framework import serializers
from .models import (
    RetirementScenario,
    CalculationResult,
    WithdrawalBucket,
    BucketedWithdrawalResult,
    SensitivityAnalysis,
    WithdrawalStrategy,
    TaxEstimate,
)


class WithdrawalBucketSerializer(serializers.ModelSerializer):
    """Serializer for WithdrawalBucket model."""

    age_range_display = serializers.CharField(source='get_age_range_display', read_only=True)

    class Meta:
        model = WithdrawalBucket
        fields = [
            'id',
            'scenario',
            'bucket_name',
            'description',
            'order',
            'start_age',
            'end_age',
            'start_year',
            'end_year',
            'age_range_display',
            'target_withdrawal_rate',
            'min_withdrawal_amount',
            'max_withdrawal_amount',
            'manual_withdrawal_override',
            'allowed_account_types',
            'prohibited_account_types',
            'withdrawal_order',
            'tax_loss_harvesting_enabled',
            'roth_conversion_enabled',
            'healthcare_cost_adjustment',
            'expected_pension_income',
            'expected_social_security_income',
            'created_date',
            'updated_date',
        ]
        read_only_fields = ['id', 'created_date', 'updated_date']


class BucketedWithdrawalResultSerializer(serializers.ModelSerializer):
    """Serializer for BucketedWithdrawalResult model."""

    bucket_name = serializers.CharField(source='bucket.bucket_name', read_only=True)

    class Meta:
        model = BucketedWithdrawalResult
        fields = [
            'id',
            'calculation',
            'bucket',
            'bucket_name',
            'year',
            'age',
            'target_rate',
            'calculated_withdrawal',
            'actual_withdrawal',
            'withdrawal_accounts',
            'portfolio_value_start',
            'investment_growth',
            'portfolio_value_end',
            'pension_income',
            'social_security_income',
            'total_available_income',
            'notes',
            'flags',
        ]
        read_only_fields = ['id']


class RetirementScenarioSerializer(serializers.ModelSerializer):
    """Basic serializer for RetirementScenario model."""

    class Meta:
        model = RetirementScenario
        fields = [
            'id',
            'user',
            'name',
            'description',
            'calculator_type',
            'parameters',
            'is_default',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class RetirementScenarioDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for RetirementScenario with related buckets."""

    withdrawal_buckets = WithdrawalBucketSerializer(many=True, read_only=True)

    class Meta:
        model = RetirementScenario
        fields = [
            'id',
            'user',
            'name',
            'description',
            'calculator_type',
            'parameters',
            'is_default',
            'withdrawal_buckets',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CalculationResultSerializer(serializers.ModelSerializer):
    """Serializer for CalculationResult model."""

    class Meta:
        model = CalculationResult
        fields = [
            'id',
            'scenario',
            'status',
            'result_data',
            'execution_time_ms',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CalculationResultDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for CalculationResult with bucketed results."""

    bucketed_results = BucketedWithdrawalResultSerializer(many=True, read_only=True)
    scenario = RetirementScenarioSerializer(read_only=True)

    class Meta:
        model = CalculationResult
        fields = [
            'id',
            'scenario',
            'status',
            'result_data',
            'bucketed_results',
            'execution_time_ms',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SensitivityAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for SensitivityAnalysis model."""

    scenario_name = serializers.CharField(source='scenario.name', read_only=True)

    class Meta:
        model = SensitivityAnalysis
        fields = [
            'id',
            'scenario',
            'scenario_name',
            'name',
            'description',
            'return_adjustment',
            'spending_adjustment',
            'inflation_adjustment',
            'return_range_min',
            'return_range_max',
            'return_step',
            'spending_range_min',
            'spending_range_max',
            'spending_step',
            'inflation_range_min',
            'inflation_range_max',
            'inflation_step',
            'result_data',
            'execution_time_ms',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'scenario_name', 'result_data', 'execution_time_ms', 'created_at', 'updated_at']


class SensitivityCalculationRequestSerializer(serializers.Serializer):
    """Serializer for sensitivity calculation requests."""

    return_adjustment = serializers.FloatField(default=0.0, help_text="Adjustment to return rate (e.g., -0.02 for -2%)")
    spending_adjustment = serializers.FloatField(default=0.0, help_text="Adjustment to spending (e.g., 0.20 for +20%)")
    inflation_adjustment = serializers.FloatField(default=0.0, help_text="Adjustment to inflation (e.g., 0.01 for +1%)")


class TornadoChartRequestSerializer(serializers.Serializer):
    """Serializer for tornado chart generation requests."""

    return_range_min = serializers.FloatField(default=-0.05)
    return_range_max = serializers.FloatField(default=0.05)
    return_step = serializers.FloatField(default=0.01)

    spending_range_min = serializers.FloatField(default=0.0)
    spending_range_max = serializers.FloatField(default=0.50)
    spending_step = serializers.FloatField(default=0.10)

    inflation_range_min = serializers.FloatField(default=0.0)
    inflation_range_max = serializers.FloatField(default=0.04)
    inflation_step = serializers.FloatField(default=0.01)


class WithdrawalStrategySerializer(serializers.ModelSerializer):
    """Serializer for WithdrawalStrategy model."""

    strategy_type_display = serializers.CharField(source='get_strategy_type_display', read_only=True)
    scenario_name = serializers.CharField(source='scenario.name', read_only=True)

    class Meta:
        model = WithdrawalStrategy
        fields = [
            'id',
            'scenario',
            'scenario_name',
            'name',
            'description',
            'strategy_type',
            'strategy_type_display',
            'taxable_percentage',
            'traditional_percentage',
            'roth_percentage',
            'hsa_percentage',
            'preserve_roth_growth',
            'minimize_social_security_taxation',
            'result_data',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'scenario_name', 'strategy_type_display', 'result_data', 'created_at', 'updated_at']


class TaxEstimateSerializer(serializers.ModelSerializer):
    """Serializer for TaxEstimate model."""

    withdrawal_strategy_name = serializers.CharField(source='withdrawal_strategy.name', read_only=True, allow_null=True)

    class Meta:
        model = TaxEstimate
        fields = [
            'id',
            'scenario',
            'withdrawal_strategy',
            'withdrawal_strategy_name',
            'year',
            'age',
            'gross_withdrawal',
            'taxable_withdrawal',
            'tax_deferred_withdrawal',
            'roth_withdrawal',
            'hsa_withdrawal',
            'ordinary_income',
            'capital_gains_income',
            'social_security_taxable',
            'agi',
            'magi',
            'federal_tax',
            'state_tax',
            'niit_tax',
            'medicare_surcharge',
            'total_tax',
            'effective_tax_rate',
            'after_tax_amount',
            'created_at',
        ]
        read_only_fields = ['id', 'withdrawal_strategy_name', 'created_at']


class TaxCalculationRequestSerializer(serializers.Serializer):
    """Serializer for tax calculation requests."""

    withdrawal_strategy_id = serializers.IntegerField(required=False, allow_null=True)
    annual_withdrawal = serializers.DecimalField(max_digits=12, decimal_places=2)
    year = serializers.IntegerField(required=False, default=1)


class StrategyComparisonRequestSerializer(serializers.Serializer):
    """Serializer for withdrawal strategy comparison requests."""

    strategy_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'taxable_first',
            'tax_deferred_first',
            'roth_first',
            'optimized',
            'custom'
        ]),
        min_length=1,
        max_length=5
    )
    annual_withdrawal = serializers.DecimalField(max_digits=12, decimal_places=2)
