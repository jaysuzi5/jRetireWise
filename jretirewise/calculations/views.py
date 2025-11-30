"""
Views for calculations.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class CalculationView(APIView):
    """Handle calculation requests."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Submit a calculation request."""
        pass
