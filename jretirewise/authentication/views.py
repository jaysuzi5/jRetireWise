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
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer
from jretirewise.financial.models import FinancialProfile, TaxProfile
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
    permission_classes = [AllowAny]

    def get(self, request):
        """Logout endpoint (GET redirect)."""
        auth_logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('account_login')

    def post(self, request):
        """Logout endpoint (POST API)."""
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

        # Validate using serializer
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save the validated data
        serializer.save()

        # Return updated user data
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data)


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

        # Get portfolio if it exists
        try:
            context['portfolio'] = user.portfolio
        except:
            context['portfolio'] = None

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

        # Get or create financial profile
        try:
            profile = FinancialProfile.objects.get(user=user)
            context['financial_profile'] = profile
        except FinancialProfile.DoesNotExist:
            context['financial_profile'] = None

        # Initialize unified form
        if 'form' not in context:
            try:
                profile = FinancialProfile.objects.get(user=user)
                context['form'] = FinancialProfileForm(instance=profile)
            except FinancialProfile.DoesNotExist:
                context['form'] = FinancialProfileForm()

        return context

    def post(self, request, *args, **kwargs):
        """Handle unified profile form submission."""
        user = request.user

        # Get or create financial profile
        try:
            profile = FinancialProfile.objects.get(user=user)
        except FinancialProfile.DoesNotExist:
            profile = None

        # Process unified form
        form = FinancialProfileForm(request.POST, instance=profile)

        if form.is_valid():
            # Save financial profile
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            # Get or create and save tax profile
            try:
                tax_profile = TaxProfile.objects.get(user=user)
            except TaxProfile.DoesNotExist:
                tax_profile = TaxProfile(user=user)

            # Update tax profile with form data
            tax_profile.filing_status = form.cleaned_data.get('filing_status') or tax_profile.filing_status
            tax_profile.state_of_residence = form.cleaned_data.get('state_of_residence') or tax_profile.state_of_residence
            tax_profile.social_security_age_62 = form.cleaned_data.get('social_security_age_62') or 0
            tax_profile.social_security_age_65 = form.cleaned_data.get('social_security_age_65') or 0
            tax_profile.social_security_age_67 = form.cleaned_data.get('social_security_age_67') or 0
            tax_profile.social_security_age_70 = form.cleaned_data.get('social_security_age_70') or 0
            tax_profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('financial-profile')
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)
