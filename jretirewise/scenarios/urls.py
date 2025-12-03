"""
URLs for scenarios app.
"""

from django.urls import path
from .views import ScenarioListView, ScenarioDetailView, ScenarioCreateView, ScenarioUpdateView, ScenarioDeleteView

urlpatterns = [
    path('', ScenarioListView.as_view(), name='scenarios'),
    path('create/', ScenarioCreateView.as_view(), name='scenario-create'),
    path('<int:pk>/', ScenarioDetailView.as_view(), name='scenario-detail'),
    path('<int:pk>/edit/', ScenarioUpdateView.as_view(), name='scenario-edit'),
    path('<int:pk>/delete/', ScenarioDeleteView.as_view(), name='scenario-delete'),
]
