"""
Views for financial data management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import csv
from django.http import HttpResponse
from datetime import datetime

from .models import (
    FinancialProfile,
    Asset,
    IncomeSource,
    Expense,
    Portfolio,
    Account,
    AccountValueHistory,
    PortfolioSnapshot,
)
from .serializers import (
    FinancialProfileSerializer,
    AssetSerializer,
    IncomeSourceSerializer,
    ExpenseSerializer,
    PortfolioSerializer,
    PortfolioDetailedSerializer,
    AccountSerializer,
    AccountDetailedSerializer,
    AccountValueHistorySerializer,
    PortfolioSnapshotSerializer,
    TaxProfileSerializer,
)


# ============================================================================
# Phase 1 ViewSets (Existing)
# ============================================================================


class FinancialProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user financial profiles."""

    serializer_class = FinancialProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Users can only see their own profile."""
        return FinancialProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user."""
        serializer.save(user=self.request.user)


class AssetViewSet(viewsets.ModelViewSet):
    """ViewSet for user assets."""

    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['asset_type', 'user']
    ordering_fields = ['created_at', 'updated_at', 'current_value']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Users can only see their own assets."""
        return Asset.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user."""
        serializer.save(user=self.request.user)


class IncomeSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for user income sources."""

    serializer_class = IncomeSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['income_type', 'is_active', 'user']
    ordering_fields = ['created_at', 'updated_at', 'annual_amount']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Users can only see their own income sources."""
        return IncomeSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user."""
        serializer.save(user=self.request.user)


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for user expenses."""

    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['expense_type', 'frequency', 'is_active', 'user']
    ordering_fields = ['created_at', 'updated_at', 'amount']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Users can only see their own expenses."""
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user."""
        serializer.save(user=self.request.user)


# ============================================================================
# Phase 2.0 ViewSets (Advanced Portfolio Management)
# ============================================================================


class PortfolioViewSet(viewsets.ModelViewSet):
    """ViewSet for user portfolios."""

    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_date', 'updated_date']
    ordering = ['-updated_date']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, basic for list."""
        if self.action == 'retrieve':
            return PortfolioDetailedSerializer
        return PortfolioSerializer

    def get_queryset(self):
        """Users can only see their own portfolio."""
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get portfolio summary with account breakdown."""
        portfolio = self.get_object()
        serializer = PortfolioDetailedSerializer(portfolio)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def accounts_by_type(self, request, pk=None):
        """Get accounts grouped by type with totals."""
        portfolio = self.get_object()
        accounts_by_type = portfolio.get_accounts_by_type()
        result = {}
        for account_type, data in accounts_by_type.items():
            result[account_type] = {
                'accounts': AccountSerializer(
                    data['accounts'],
                    many=True
                ).data,
                'total_value': float(data['total_value']),
            }
        return Response(result)


class AccountViewSet(viewsets.ModelViewSet):
    """ViewSet for individual investment accounts."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['portfolio', 'account_type', 'status', 'tax_treatment']
    ordering_fields = ['withdrawal_priority', 'account_name', 'created_date', 'current_value']
    ordering = ['withdrawal_priority', 'account_name']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, basic for list."""
        if self.action == 'retrieve':
            return AccountDetailedSerializer
        return AccountSerializer

    def get_queryset(self):
        """Users can only see accounts in their portfolio."""
        portfolio = Portfolio.objects.filter(user=self.request.user).first()
        if portfolio:
            return Account.objects.filter(portfolio=portfolio)
        return Account.objects.none()

    def perform_create(self, serializer):
        """Set portfolio from query parameter or user's portfolio."""
        portfolio_id = self.request.query_params.get('portfolio')
        if portfolio_id:
            portfolio = Portfolio.objects.get(id=portfolio_id, user=self.request.user)
        else:
            portfolio = Portfolio.objects.get(user=self.request.user)
        serializer.save(portfolio=portfolio)

    def perform_update(self, serializer):
        """Update account, preventing portfolio change."""
        serializer.save()

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get account's value history."""
        account = self.get_object()
        history = account.value_history.all()
        serializer = AccountValueHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def record_value(self, request, pk=None):
        """Record a new value snapshot for the account."""
        account = self.get_object()
        serializer = AccountValueHistorySerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(account=account, recorded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def effective_metrics(self, request, pk=None):
        """Get calculated metrics for the account."""
        account = self.get_object()
        return Response({
            'effective_growth_rate': float(account.get_effective_growth_rate()),
            'annual_contribution': float(account.get_annual_contribution()),
            'is_active': account.status == 'active',
        })

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export account list to CSV format."""
        # Get the filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="accounts-{datetime.now().strftime("%Y%m%d-%H%M%S")}.csv"'

        writer = csv.writer(response)

        # Write header
        writer.writerow([
            'Account Name',
            'Account Type',
            'Current Value',
            'Default Growth Rate (%)',
            'Tax Treatment',
            'Status',
            'Institution',
            'Account Number',
            'Created Date'
        ])

        # Write data rows
        for account in queryset.select_related('portfolio'):
            writer.writerow([
                account.account_name,
                account.get_account_type_display(),
                f'{float(account.current_value):.2f}',
                f'{float(account.default_growth_rate):.2f}',
                account.get_tax_treatment_display(),
                account.get_status_display(),
                account.institution_name or '',
                account.account_number or '',
                account.created_date.strftime('%Y-%m-%d') if account.created_date else ''
            ])

        return response


class AccountValueHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for account value history."""

    serializer_class = AccountValueHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['account', 'source', 'recorded_date']
    ordering_fields = ['recorded_date', 'recorded_timestamp', 'value']
    ordering = ['-recorded_date']

    def get_queryset(self):
        """Users can only see history for their accounts."""
        queryset = AccountValueHistory.objects.none()

        portfolio = Portfolio.objects.filter(user=self.request.user).first()
        if portfolio:
            accounts = Account.objects.filter(portfolio=portfolio)
            queryset = AccountValueHistory.objects.filter(account__in=accounts)

            # Apply date-range filtering if provided
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')

            if start_date:
                try:
                    queryset = queryset.filter(recorded_date__gte=start_date)
                except (ValueError, TypeError):
                    pass  # Invalid date format, ignore filter

            if end_date:
                try:
                    queryset = queryset.filter(recorded_date__lte=end_date)
                except (ValueError, TypeError):
                    pass  # Invalid date format, ignore filter

        return queryset

    def perform_create(self, serializer):
        """Set recorded_by to current user."""
        serializer.save(recorded_by=self.request.user)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export account value history to CSV format."""
        # Get the filtered queryset
        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="account-history-{datetime.now().strftime("%Y%m%d-%H%M%S")}.csv"'

        writer = csv.writer(response)

        # Write header
        writer.writerow([
            'Account Name',
            'Account Type',
            'Recorded Date',
            'Value',
            'Source',
            'Notes',
            'Recorded By'
        ])

        # Write data rows
        for history in queryset.select_related('account', 'recorded_by'):
            writer.writerow([
                history.account.account_name,
                history.account.get_account_type_display(),
                history.recorded_date.strftime('%Y-%m-%d'),
                f'{float(history.value):.2f}',
                history.get_source_display(),
                history.notes or '',
                history.recorded_by.email if history.recorded_by else ''
            ])

        return response


class PortfolioSnapshotViewSet(viewsets.ModelViewSet):
    """ViewSet for portfolio snapshots."""

    serializer_class = PortfolioSnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['portfolio', 'snapshot_date']
    ordering_fields = ['snapshot_date', 'created_timestamp', 'total_value']
    ordering = ['-snapshot_date']

    def get_queryset(self):
        """Users can only see snapshots for their portfolio."""
        portfolio = Portfolio.objects.filter(user=self.request.user).first()
        if portfolio:
            return PortfolioSnapshot.objects.filter(portfolio=portfolio)
        return PortfolioSnapshot.objects.none()

    @action(detail=False, methods=['post'])
    def create_snapshot(self, request):
        """Create a new snapshot of the portfolio."""
        portfolio_id = request.data.get('portfolio')
        portfolio = Portfolio.objects.get(id=portfolio_id, user=request.user)

        snapshot = PortfolioSnapshot.objects.create(
            portfolio=portfolio,
            total_value=portfolio.get_total_value(),
            snapshot_date=request.data.get('snapshot_date'),
            calculated_from=request.data.get('calculated_from', 'all_accounts'),
            notes=request.data.get('notes', ''),
        )

        serializer = self.get_serializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def compare_to_previous(self, request, pk=None):
        """Compare snapshot to previous snapshot."""
        snapshot = self.get_object()
        previous = PortfolioSnapshot.objects.filter(
            portfolio=snapshot.portfolio,
            snapshot_date__lt=snapshot.snapshot_date
        ).order_by('-snapshot_date').first()

        if not previous:
            return Response({'message': 'No previous snapshot found'})

        difference = snapshot.total_value - previous.total_value
        percent_change = (difference / previous.total_value * 100) if previous.total_value > 0 else 0

        return Response({
            'current': {
                'date': snapshot.snapshot_date,
                'value': float(snapshot.total_value),
            },
            'previous': {
                'date': previous.snapshot_date,
                'value': float(previous.total_value),
            },
            'difference': float(difference),
            'percent_change': float(percent_change),
        })


# ============================================================================
# Phase 2 Tax Planning ViewSets
# ============================================================================


class TaxProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user tax profile management.

    Handles tax information including filing status, state of residence,
    account balances, and Social Security benefits by claiming age.
    """

    serializer_class = TaxProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's tax profile."""
        from .models import TaxProfile
        return TaxProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user to current user when creating tax profile."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='me', url_name='tax-profile-me')
    def current_user_profile(self, request):
        """
        Get the current user's tax profile (or 404 if not exists).

        GET /api/v1/tax-profiles/me/
        """
        from .models import TaxProfile
        try:
            tax_profile = request.user.tax_profile
            serializer = TaxProfileSerializer(tax_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TaxProfile.DoesNotExist:
            return Response(
                {'error': 'Tax profile not found. Create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )
