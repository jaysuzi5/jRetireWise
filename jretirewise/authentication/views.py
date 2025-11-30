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
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from jretirewise.financial.models import FinancialProfile
from jretirewise.financial.forms import FinancialProfileForm
from jretirewise.scenarios.models import RetirementScenario


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
        auth_logout(request)
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
    template_name = 'jretirewise/dashboard.html'
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        """Add context data for dashboard."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            context['financial_profile'] = FinancialProfile.objects.get(user=user)
        except FinancialProfile.DoesNotExist:
            context['financial_profile'] = None

        context['scenarios'] = RetirementScenario.objects.filter(user=user).order_by('-updated_at')[:5]
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile template view."""
    template_name = 'jretirewise/profile.html'
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        """Add context data for profile."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            profile = FinancialProfile.objects.get(user=user)
            context['financial_profile'] = profile
            if 'form' not in context:
                context['form'] = FinancialProfileForm(instance=profile)
        except FinancialProfile.DoesNotExist:
            context['financial_profile'] = None
            if 'form' not in context:
                context['form'] = FinancialProfileForm()

        return context

    def post(self, request, *args, **kwargs):
        """Handle profile form submission."""
        user = request.user
        try:
            profile = FinancialProfile.objects.get(user=user)
            form = FinancialProfileForm(request.POST, instance=profile)
        except FinancialProfile.DoesNotExist:
            form = FinancialProfileForm(request.POST)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Financial profile updated successfully!')
            return redirect('financial-profile')
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
