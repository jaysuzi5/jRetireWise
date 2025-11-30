"""
Views for scenario management.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import RetirementScenario


class ScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet for RetirementScenario management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)
