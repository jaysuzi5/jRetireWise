"""
Views for scenario management.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from decimal import Decimal
from .models import RetirementScenario, WithdrawalBucket, CalculationResult, BucketedWithdrawalResult
from .forms import ScenarioForm
from .serializers import (
    RetirementScenarioSerializer, WithdrawalBucketSerializer,
    CalculationResultSerializer, CalculationResultDetailSerializer,
    BucketedWithdrawalResultSerializer
)
from jretirewise.calculations.calculators import DynamicBucketedWithdrawalCalculator
import json
import logging
import time

# Get a logger instance
logger = logging.getLogger(__name__)


class ScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet for RetirementScenario management."""
    permission_classes = [IsAuthenticated]
    serializer_class = RetirementScenarioSerializer

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the current user as the owner."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='buckets', url_name='scenario-buckets')
    def list_buckets(self, request, pk=None):
        """List all withdrawal buckets for a scenario."""
        scenario = self.get_object()
        buckets = scenario.withdrawal_buckets.all().order_by('order', 'start_age')
        serializer = WithdrawalBucketSerializer(buckets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='buckets', url_name='scenario-create-bucket')
    def create_bucket(self, request, pk=None):
        """Create a new withdrawal bucket for a scenario."""
        scenario = self.get_object()
        serializer = WithdrawalBucketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(scenario=scenario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='calculate/bucketed-withdrawal', url_name='calculate-bucketed')
    def calculate_bucketed_withdrawal(self, request, pk=None):
        """Run a bucketed withdrawal calculation for a scenario."""
        scenario = self.get_object()

        # Validate scenario has required parameters
        params = scenario.parameters
        if not all(k in params for k in ['portfolio_value', 'retirement_age', 'life_expectancy']):
            return Response(
                {'error': 'Scenario missing required parameters: portfolio_value, retirement_age, life_expectancy'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all withdrawal buckets for scenario
        buckets = scenario.withdrawal_buckets.all().order_by('order', 'start_age')
        if not buckets.exists():
            return Response(
                {'error': 'Scenario has no withdrawal buckets defined'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert buckets to dictionaries for calculator
        bucket_dicts = []
        for bucket in buckets:
            bucket_dict = {
                'bucket_name': bucket.bucket_name,
                'start_age': bucket.start_age,
                'end_age': bucket.end_age,
                'target_withdrawal_rate': bucket.target_withdrawal_rate,
                'min_withdrawal_amount': float(bucket.min_withdrawal_amount) if bucket.min_withdrawal_amount else None,
                'max_withdrawal_amount': float(bucket.max_withdrawal_amount) if bucket.max_withdrawal_amount else None,
                'manual_withdrawal_override': float(bucket.manual_withdrawal_override) if bucket.manual_withdrawal_override else None,
                'expected_pension_income': float(bucket.expected_pension_income),
                'expected_social_security_income': float(bucket.expected_social_security_income),
                'healthcare_cost_adjustment': float(bucket.healthcare_cost_adjustment),
                'tax_loss_harvesting_enabled': bucket.tax_loss_harvesting_enabled,
                'roth_conversion_enabled': bucket.roth_conversion_enabled,
                'allowed_account_types': bucket.allowed_account_types,
                'prohibited_account_types': bucket.prohibited_account_types,
                'withdrawal_order': bucket.withdrawal_order,
            }
            bucket_dicts.append(bucket_dict)

        try:
            # Run calculation
            start_time = time.time()
            calculator = DynamicBucketedWithdrawalCalculator(
                portfolio_value=Decimal(str(params['portfolio_value'])),
                retirement_age=params['retirement_age'],
                life_expectancy=params['life_expectancy'],
                annual_return_rate=params.get('annual_return_rate', 0.07),
                inflation_rate=params.get('inflation_rate', 0.03)
            )
            result_data = calculator.calculate(bucket_dicts)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Store result in database
            calculation_result, created = CalculationResult.objects.update_or_create(
                scenario=scenario,
                defaults={
                    'status': 'completed',
                    'result_data': result_data,
                    'execution_time_ms': execution_time_ms,
                    'error_message': ''
                }
            )

            # Store individual year results
            BucketedWithdrawalResult.objects.filter(calculation=calculation_result).delete()
            for projection in result_data.get('projections', []):
                BucketedWithdrawalResult.objects.create(
                    calculation=calculation_result,
                    bucket=buckets.filter(bucket_name=projection['bucket_name']).first(),
                    year=projection['year'],
                    age=projection['age'],
                    target_rate=projection['target_rate'],
                    calculated_withdrawal=Decimal(str(projection['calculated_withdrawal'])),
                    actual_withdrawal=Decimal(str(projection['actual_withdrawal'])),
                    portfolio_value_start=Decimal(str(projection['portfolio_value_start'])),
                    investment_growth=Decimal(str(projection['investment_growth'])),
                    portfolio_value_end=Decimal(str(projection['portfolio_value_end'])),
                    pension_income=Decimal(str(projection['pension_income'])),
                    social_security_income=Decimal(str(projection['social_security_income'])),
                    total_available_income=Decimal(str(projection['total_available_income'])),
                    notes=projection['notes'],
                    flags=projection['flags'],
                    withdrawal_accounts={}
                )

            serializer = CalculationResultDetailSerializer(calculation_result)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Bucketed withdrawal calculation failed: {str(e)}")
            # Store error result
            calculation_result, _ = CalculationResult.objects.update_or_create(
                scenario=scenario,
                defaults={
                    'status': 'failed',
                    'result_data': {},
                    'error_message': str(e)
                }
            )
            return Response(
                {'error': f'Calculation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawalBucketViewSet(viewsets.ModelViewSet):
    """ViewSet for WithdrawalBucket management."""
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalBucketSerializer

    def get_queryset(self):
        """Filter buckets to only those for scenarios owned by the current user."""
        return WithdrawalBucket.objects.filter(scenario__user=self.request.user)

    def perform_create(self, serializer):
        """Create a new bucket for a scenario."""
        # Ensure the scenario belongs to the current user
        scenario_id = self.request.data.get('scenario')
        try:
            scenario = RetirementScenario.objects.get(id=scenario_id, user=self.request.user)
            serializer.save(scenario=scenario)
        except RetirementScenario.DoesNotExist:
            raise PermissionError("You do not have permission to add buckets to this scenario")

    def perform_update(self, serializer):
        """Update a bucket."""
        serializer.save()

    @action(detail=False, methods=['get'], url_path='scenario/(?P<scenario_id>\d+)')
    def by_scenario(self, request, scenario_id=None):
        """Get all buckets for a specific scenario."""
        try:
            scenario = RetirementScenario.objects.get(id=scenario_id, user=request.user)
            buckets = scenario.withdrawal_buckets.all().order_by('order', 'start_age')
            serializer = WithdrawalBucketSerializer(buckets, many=True)
            return Response(serializer.data)
        except RetirementScenario.DoesNotExist:
            return Response(
                {'error': 'Scenario not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], url_path='validate-overlap')
    def validate_overlap(self, request):
        """Validate that bucket age ranges don't have gaps or overlaps."""
        buckets_data = request.data.get('buckets', [])
        if not buckets_data:
            return Response({'valid': True, 'errors': []})

        # Sort buckets by start_age
        sorted_buckets = sorted(
            [b for b in buckets_data if b.get('start_age')],
            key=lambda x: x['start_age']
        )

        errors = []

        # Check for overlaps
        for i in range(len(sorted_buckets) - 1):
            current = sorted_buckets[i]
            next_bucket = sorted_buckets[i + 1]

            current_end = current.get('end_age') or float('inf')
            next_start = next_bucket.get('start_age')

            if next_start <= current_end:
                errors.append(
                    f"Bucket '{current['bucket_name']}' overlaps with '{next_bucket['bucket_name']}'"
                )

        # Check for gaps
        for i in range(len(sorted_buckets) - 1):
            current = sorted_buckets[i]
            next_bucket = sorted_buckets[i + 1]

            current_end = current.get('end_age')
            next_start = next_bucket.get('start_age')

            # Only check if current bucket has an end_age
            if current_end and next_start and next_start > current_end + 1:
                errors.append(
                    f"Gap between '{current['bucket_name']}' (ends at {current_end}) "
                    f"and '{next_bucket['bucket_name']}' (starts at {next_start})"
                )

        return Response({
            'valid': len(errors) == 0,
            'errors': errors
        })


class ScenarioListView(LoginRequiredMixin, ListView):
    """List all scenarios for the current user."""
    model = RetirementScenario
    template_name = 'jretirewise/scenario_list.html'
    context_object_name = 'scenarios'
    paginate_by = 20

    def get_queryset(self):
        logger.info("List all scenarios for the current user.")
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


class ScenarioDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a retirement scenario."""
    model = RetirementScenario
    success_url = reverse_lazy('scenarios')

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Show success message on deletion."""
        scenario = self.get_object()
        messages.success(request, f'Scenario "{scenario.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)
