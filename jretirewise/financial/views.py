"""
Views for financial data management.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Asset, IncomeSource, Expense, FinancialProfile


class AssetViewSet(viewsets.ModelViewSet):
    """ViewSet for Asset management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Asset.objects.filter(user=self.request.user)


class IncomeSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for IncomeSource management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IncomeSource.objects.filter(user=self.request.user)


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for Expense management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)


class FinancialProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for FinancialProfile management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialProfile.objects.filter(user=self.request.user)
