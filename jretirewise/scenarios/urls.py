"""
URLs for scenarios app.
"""

from django.urls import path
from .views import (
    ScenarioListView, ScenarioDetailView, ScenarioCreateView,
    ScenarioUpdateView, ScenarioDeleteView,
    MonteCarloScenarioCreateView, MonteCarloScenarioUpdateView,
)

urlpatterns = [
    path('', ScenarioListView.as_view(), name='scenarios'),
    path('create/', ScenarioCreateView.as_view(), name='scenario-create'),
    path('monte-carlo/create/', MonteCarloScenarioCreateView.as_view(), name='scenario-monte-carlo-create'),
    path('<int:pk>/', ScenarioDetailView.as_view(), name='scenario-detail'),
    path('<int:pk>/edit/', ScenarioUpdateView.as_view(), name='scenario-edit'),
    path('monte-carlo/<int:pk>/edit/', MonteCarloScenarioUpdateView.as_view(), name='scenario-monte-carlo-edit'),
    path('<int:pk>/delete/', ScenarioDeleteView.as_view(), name='scenario-delete'),
]
