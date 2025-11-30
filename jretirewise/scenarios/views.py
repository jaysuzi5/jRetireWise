"""
Views for scenario management.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import RetirementScenario
from .forms import ScenarioForm
import json


class ScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet for RetirementScenario management."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)


class ScenarioListView(LoginRequiredMixin, ListView):
    """List all scenarios for the current user."""
    model = RetirementScenario
    template_name = 'jretirewise/scenario_list.html'
    context_object_name = 'scenarios'
    paginate_by = 20

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user).order_by('-updated_at')


class ScenarioDetailView(LoginRequiredMixin, DetailView):
    """Display a specific scenario with results."""
    model = RetirementScenario
    template_name = 'jretirewise/scenario_detail.html'
    context_object_name = 'scenario'

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add result data to context."""
        context = super().get_context_data(**kwargs)
        scenario = self.get_object()
        if hasattr(scenario, 'result') and scenario.result:
            context['result'] = scenario.result
            # Parse result_data if it's a JSON string
            if isinstance(scenario.result.result_data, str):
                context['result_data'] = json.loads(scenario.result.result_data)
            else:
                context['result_data'] = scenario.result.result_data
        return context


class ScenarioCreateView(LoginRequiredMixin, CreateView):
    """Create a new retirement scenario."""
    model = RetirementScenario
    form_class = ScenarioForm
    template_name = 'jretirewise/scenario_form.html'
    success_url = reverse_lazy('scenarios')

    def form_valid(self, form):
        """Set the current user as the owner."""
        form.instance.user = self.request.user
        messages.success(self.request, f'Scenario "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class ScenarioUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing retirement scenario."""
    model = RetirementScenario
    form_class = ScenarioForm
    template_name = 'jretirewise/scenario_form.html'
    success_url = reverse_lazy('scenarios')

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Show success message."""
        messages.success(self.request, f'Scenario "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
