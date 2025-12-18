"""
Serializers for scenario and calculation models.
"""

from rest_framework import serializers
from .models import RetirementScenario, CalculationResult, WithdrawalBucket, BucketedWithdrawalResult, SensitivityAnalysis


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
