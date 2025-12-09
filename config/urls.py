"""
URL configuration for jRetireWise project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from jretirewise.authentication.views import LoginView, LogoutView, UserProfileView
from jretirewise.financial.views import (
    AssetViewSet, IncomeSourceViewSet, ExpenseViewSet, FinancialProfileViewSet,
    PortfolioViewSet, AccountViewSet, AccountValueHistoryViewSet, PortfolioSnapshotViewSet,
)
from jretirewise.scenarios.views import ScenarioViewSet, WithdrawalBucketViewSet
from jretirewise.calculations.views import CalculationView


# Health check views
def health_ready(request):
    """Kubernetes readiness probe endpoint."""
    return JsonResponse({'status': 'ready'})


def health_live(request):
    """Kubernetes liveness probe endpoint."""
    return JsonResponse({'status': 'alive'})

# API Router
router = DefaultRouter()
# Phase 1 endpoints
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'income-sources', IncomeSourceViewSet, basename='income-source')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'financial-profile', FinancialProfileViewSet, basename='financial-profile')
router.register(r'scenarios', ScenarioViewSet, basename='scenario')
# Phase 2.1 endpoints
router.register(r'withdrawal-buckets', WithdrawalBucketViewSet, basename='withdrawal-bucket')
# Phase 2.0 endpoints
router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'account-history', AccountValueHistoryViewSet, basename='account-history')
router.register(r'portfolio-snapshots', PortfolioSnapshotViewSet, basename='portfolio-snapshot')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('auth/accounts/', include('allauth.urls')),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # API
    path('api/v1/', include(router.urls)),
    path('api/v1/calculations/', CalculationView.as_view(), name='api-calculation'),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Template views
    path('', include('jretirewise.authentication.urls')),
    path('dashboard/', include('jretirewise.scenarios.urls')),
    path('financial/', include('jretirewise.financial.urls')),

    # Health checks
    path('health/ready/', health_ready, name='health-ready'),
    path('health/live/', health_live, name='health-live'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
