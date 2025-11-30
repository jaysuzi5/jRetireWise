"""
URLs for authentication app.
"""

from django.urls import path
from .views import DashboardView, ProfileView

app_name = 'authentication'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
