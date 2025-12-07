"""
URLs for financial app.
"""

from django.urls import path
from .portfolio_views import (
    PortfolioListView,
    PortfolioDetailView,
    PortfolioCreateView,
    PortfolioUpdateView,
    PortfolioDeleteView,
    AccountDetailView,
    AccountCreateView,
    AccountUpdateView,
    AccountDeleteView,
    AccountRecordValueView,
)

app_name = 'financial'

urlpatterns = [
    # Portfolio URLs
    path('portfolios/', PortfolioListView.as_view(), name='portfolio-list'),
    path('portfolios/<int:pk>/', PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('portfolios/create/', PortfolioCreateView.as_view(), name='portfolio-create'),
    path('portfolios/<int:pk>/edit/', PortfolioUpdateView.as_view(), name='portfolio-edit'),
    path('portfolios/<int:pk>/delete/', PortfolioDeleteView.as_view(), name='portfolio-delete'),

    # Account URLs
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('portfolios/<int:portfolio_id>/accounts/create/', AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/edit/', AccountUpdateView.as_view(), name='account-edit'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account-delete'),

    # Account Value Recording URLs
    path('accounts/<int:account_id>/record-value/', AccountRecordValueView.as_view(), name='account-record-value'),
]
