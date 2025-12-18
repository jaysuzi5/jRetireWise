"""
DRF Serializers for financial models including Phase 2.0 portfolio management.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    FinancialProfile,
    Asset,
    IncomeSource,
    Expense,
    Portfolio,
    Account,
    AccountValueHistory,
    PortfolioSnapshot,
    TaxProfile,
)


# ============================================================================
# Phase 1 Serializers (Existing)
# ============================================================================


class FinancialProfileSerializer(serializers.ModelSerializer):
    """Serializer for user financial profile."""

    class Meta:
        model = FinancialProfile
        fields = [
            'id',
            'user',
            'current_age',
            'retirement_age',
            'life_expectancy',
            'annual_spending',
            'social_security_annual',
            'pension_annual',
            'current_portfolio_value',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for user assets."""

    class Meta:
        model = Asset
        fields = [
            'id',
            'user',
            'name',
            'asset_type',
            'current_value',
            'annual_return_rate',
            'allocation_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class IncomeSourceSerializer(serializers.ModelSerializer):
    """Serializer for user income sources."""

    class Meta:
        model = IncomeSource
        fields = [
            'id',
            'user',
            'name',
            'income_type',
            'annual_amount',
            'start_age',
            'end_age',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for user expenses."""

    class Meta:
        model = Expense
        fields = [
            'id',
            'user',
            'name',
            'expense_type',
            'amount',
            'frequency',
            'start_age',
            'end_age',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# Phase 2.0 Serializers (Advanced Portfolio Management)
# ============================================================================


class AccountValueHistorySerializer(serializers.ModelSerializer):
    """Serializer for account value history snapshots."""

    recorded_by_username = serializers.CharField(
        source='recorded_by.username',
        read_only=True,
    )

    class Meta:
        model = AccountValueHistory
        fields = [
            'id',
            'account',
            'value',
            'recorded_date',
            'recorded_timestamp',
            'recorded_by',
            'recorded_by_username',
            'source',
            'notes',
        ]
        read_only_fields = ['id', 'recorded_timestamp']

    def create(self, validated_data):
        """Set recorded_by to current user if not provided."""
        if not validated_data.get('recorded_by'):
            validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for portfolio snapshots."""

    class Meta:
        model = PortfolioSnapshot
        fields = [
            'id',
            'portfolio',
            'total_value',
            'snapshot_date',
            'created_timestamp',
            'calculated_from',
            'notes',
        ]
        read_only_fields = ['id', 'created_timestamp']


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for individual investment accounts."""

    account_type_display = serializers.CharField(
        source='get_account_type_display',
        read_only=True,
    )
    tax_treatment_display = serializers.CharField(
        source='get_tax_treatment_display',
        read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )
    data_source_display = serializers.CharField(
        source='get_data_source_display',
        read_only=True,
    )
    effective_growth_rate = serializers.SerializerMethodField()
    annual_contribution = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id',
            'portfolio',
            'account_type',
            'account_type_display',
            'account_name',
            'account_number',
            'institution_name',
            'description',
            'current_value',
            'default_growth_rate',
            'inflation_adjustment',
            'expected_contribution_rate',
            'investment_allocation',
            'withdrawal_priority',
            'withdrawal_restrictions',
            'tax_treatment',
            'tax_treatment_display',
            'rmd_age',
            'rmd_percentage',
            'status',
            'status_display',
            'data_source',
            'data_source_display',
            'created_date',
            'updated_date',
            'effective_growth_rate',
            'annual_contribution',
        ]
        read_only_fields = [
            'id',
            'created_date',
            'updated_date',
            'effective_growth_rate',
            'annual_contribution',
        ]

    def get_effective_growth_rate(self, obj):
        """Get calculated effective growth rate."""
        return float(obj.get_effective_growth_rate())

    def get_annual_contribution(self, obj):
        """Get calculated annual contribution."""
        return float(obj.get_annual_contribution())

    def validate_investment_allocation(self, value):
        """Validate that investment allocation percentages sum to 100."""
        if not value:
            return value

        total = sum(value.values())
        if total != 100:
            raise serializers.ValidationError(
                f"Investment allocation percentages must sum to 100 (current: {total})"
            )
        return value

    def validate_withdrawal_priority(self, value):
        """Validate withdrawal priority is non-negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Withdrawal priority must be non-negative"
            )
        return value


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for user's portfolio container."""

    accounts = AccountSerializer(many=True, read_only=True)
    total_value = serializers.SerializerMethodField()
    accounts_by_type = serializers.SerializerMethodField()
    account_count = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user',
            'name',
            'description',
            'created_date',
            'updated_date',
            'accounts',
            'account_count',
            'total_value',
            'accounts_by_type',
        ]
        read_only_fields = [
            'id',
            'user',
            'created_date',
            'updated_date',
            'accounts',
            'account_count',
            'total_value',
            'accounts_by_type',
        ]

    def get_total_value(self, obj):
        """Get calculated total portfolio value."""
        return float(obj.get_total_value())

    def get_account_count(self, obj):
        """Get number of active accounts."""
        return obj.accounts.filter(status='active').count()

    def get_accounts_by_type(self, obj):
        """Get accounts grouped by type with totals."""
        accounts_by_type = obj.get_accounts_by_type()
        result = {}
        for account_type, data in accounts_by_type.items():
            result[account_type] = {
                'count': len(data['accounts']),
                'total_value': float(data['total_value']),
            }
        return result

    def create(self, validated_data):
        """Set user to current user if not provided."""
        if not validated_data.get('user'):
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Prevent user from being changed."""
        validated_data.pop('user', None)
        return super().update(instance, validated_data)


class PortfolioDetailedSerializer(PortfolioSerializer):
    """Extended portfolio serializer with additional details."""

    snapshots = PortfolioSnapshotSerializer(many=True, read_only=True)
    recent_snapshots = serializers.SerializerMethodField()

    class Meta(PortfolioSerializer.Meta):
        fields = PortfolioSerializer.Meta.fields + [
            'snapshots',
            'recent_snapshots',
        ]
        read_only_fields = PortfolioSerializer.Meta.read_only_fields + [
            'snapshots',
            'recent_snapshots',
        ]

    def get_recent_snapshots(self, obj):
        """Get last 12 snapshots for trending."""
        snapshots = obj.snapshots.all()[:12]
        return PortfolioSnapshotSerializer(snapshots, many=True).data


class AccountDetailedSerializer(AccountSerializer):
    """Extended account serializer with value history."""

    value_history = AccountValueHistorySerializer(many=True, read_only=True)
    recent_history = serializers.SerializerMethodField()

    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + [
            'value_history',
            'recent_history',
        ]
        read_only_fields = AccountSerializer.Meta.read_only_fields + [
            'value_history',
            'recent_history',
        ]

    def get_recent_history(self, obj):
        """Get last 12 history entries for trending."""
        history = obj.value_history.all()[:12]
        return AccountValueHistorySerializer(history, many=True).data


# ============================================================================
# Phase 2 Tax Planning Serializers
# ============================================================================


class TaxProfileSerializer(serializers.ModelSerializer):
    """Serializer for user tax profile and withdrawal optimization."""

    filing_status_display = serializers.CharField(
        source='get_filing_status_display',
        read_only=True
    )

    # Computed fields for Social Security by claiming age
    social_security_annual_62 = serializers.SerializerMethodField()
    social_security_annual_65 = serializers.SerializerMethodField()
    social_security_annual_67 = serializers.SerializerMethodField()
    social_security_annual_70 = serializers.SerializerMethodField()

    class Meta:
        model = TaxProfile
        fields = [
            'id',
            'user',
            'filing_status',
            'filing_status_display',
            'state_of_residence',
            'full_retirement_age',
            'social_security_age_62',
            'social_security_age_65',
            'social_security_age_67',
            'social_security_age_70',
            'social_security_annual_62',
            'social_security_annual_65',
            'social_security_annual_67',
            'social_security_annual_70',
            'traditional_ira_balance',
            'roth_ira_balance',
            'taxable_account_balance',
            'hsa_balance',
            'pension_annual',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'filing_status_display',
            'social_security_annual_62',
            'social_security_annual_65',
            'social_security_annual_67',
            'social_security_annual_70',
            'created_at',
            'updated_at',
        ]

    def get_social_security_annual_62(self, obj):
        """Get annual Social Security benefit for age 62."""
        return float(obj.get_social_security_annual(62))

    def get_social_security_annual_65(self, obj):
        """Get annual Social Security benefit for age 65."""
        return float(obj.get_social_security_annual(65))

    def get_social_security_annual_67(self, obj):
        """Get annual Social Security benefit for age 67."""
        return float(obj.get_social_security_annual(67))

    def get_social_security_annual_70(self, obj):
        """Get annual Social Security benefit for age 70."""
        return float(obj.get_social_security_annual(70))
