"""
Views for authentication.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer


class LoginView(APIView):
    """Handle user login."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Login endpoint."""
        # Login is handled by django-allauth
        return Response({'status': 'Use Google OAuth for login'})


class LogoutView(APIView):
    """Handle user logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout endpoint."""
        from django.contrib.auth import logout
        logout(request)
        return Response({'status': 'logged out'})


class UserProfileView(APIView):
    """Retrieve current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Update current user profile."""
        user = request.user
        profile = user.profile

        # Update profile
        profile.full_name = request.data.get('full_name', profile.full_name)
        profile.theme_preference = request.data.get('theme_preference', profile.theme_preference)
        profile.notification_email = request.data.get('notification_email', profile.notification_email)
        profile.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard template view."""
    template_name = 'dashboard/index.html'
    login_url = 'account_login'


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile template view."""
    template_name = 'profile/index.html'
    login_url = 'account_login'
