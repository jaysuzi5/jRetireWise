"""
URLs for financial app.
"""

from django.urls import path
from .portfolio_views import (
    PortfolioRedirectView,
    PortfolioDetailView,
    AccountDetailView,
    AccountCreateView,
    AccountUpdateView,
    AccountDeleteView,
    AccountRecordValueView,
    AccountValueHistoryUpdateView,
    AccountValueHistoryDeleteView,
    TaxProfileManageView,
)

app_name = 'financial'

urlpatterns = [
    # Portfolio URLs - simplified to single portfolio per user
    path('portfolios/', PortfolioRedirectView.as_view(), name='portfolio-list'),
    path('portfolio/', PortfolioRedirectView.as_view(), name='portfolio'),
    path('portfolios/<int:pk>/', PortfolioDetailView.as_view(), name='portfolio-detail'),

    # Account URLs
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('portfolios/<int:portfolio_id>/accounts/create/', AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/edit/', AccountUpdateView.as_view(), name='account-edit'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account-delete'),

    # Account Value Recording URLs
    path('accounts/<int:account_id>/record-value/', AccountRecordValueView.as_view(), name='account-record-value'),
    path('value-history/<int:pk>/edit/', AccountValueHistoryUpdateView.as_view(), name='value-history-edit'),
    path('value-history/<int:pk>/delete/', AccountValueHistoryDeleteView.as_view(), name='value-history-delete'),

    # Tax Profile URL
    path('tax-profile/', TaxProfileManageView.as_view(), name='tax-profile'),
]
