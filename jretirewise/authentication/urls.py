"""
URLs for authentication app.
"""

from django.urls import path
from .views import DashboardView, ProfileView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='financial-profile'),
]
