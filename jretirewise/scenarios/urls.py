"""
URLs for scenarios app.
"""

from django.urls import path
from .views import (
    ScenarioListView, ScenarioDetailView, ScenarioCreateView,
    ScenarioUpdateView, ScenarioDeleteView,
    MonteCarloScenarioCreateView, MonteCarloScenarioUpdateView,
    BucketedWithdrawalScenarioCreateView, BucketedWithdrawalScenarioUpdateView,
    BucketListView, BucketCreateView, BucketUpdateView, BucketDeleteView,
    RunBucketedCalculationView,
)

urlpatterns = [
    path('', ScenarioListView.as_view(), name='scenarios'),
    path('create/', ScenarioCreateView.as_view(), name='scenario-create'),
    path('monte-carlo/create/', MonteCarloScenarioCreateView.as_view(), name='scenario-monte-carlo-create'),
    path('bucketed-withdrawal/create/', BucketedWithdrawalScenarioCreateView.as_view(), name='scenario-bucketed-create'),
    path('<int:pk>/', ScenarioDetailView.as_view(), name='scenario-detail'),
    path('<int:pk>/edit/', ScenarioUpdateView.as_view(), name='scenario-edit'),
    path('monte-carlo/<int:pk>/edit/', MonteCarloScenarioUpdateView.as_view(), name='scenario-monte-carlo-edit'),
    path('bucketed-withdrawal/<int:pk>/edit/', BucketedWithdrawalScenarioUpdateView.as_view(), name='scenario-bucketed-edit'),
    path('<int:pk>/delete/', ScenarioDeleteView.as_view(), name='scenario-delete'),
    # Bucket Management URLs
    path('<int:scenario_pk>/buckets/', BucketListView.as_view(), name='bucket-list'),
    path('<int:scenario_pk>/buckets/create/', BucketCreateView.as_view(), name='bucket-create'),
    path('<int:scenario_pk>/buckets/calculate/', RunBucketedCalculationView.as_view(), name='bucket-calculate'),
    path('buckets/<int:pk>/edit/', BucketUpdateView.as_view(), name='bucket-edit'),
    path('buckets/<int:pk>/delete/', BucketDeleteView.as_view(), name='bucket-delete'),
]
