"""
Views for scenario management.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from .models import RetirementScenario, WithdrawalBucket, CalculationResult, BucketedWithdrawalResult
from .forms import ScenarioForm, MonteCarloScenarioForm, BucketedWithdrawalScenarioForm, WithdrawalBucketForm, HistoricalScenarioForm
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


class MonteCarloScenarioCreateView(LoginRequiredMixin, CreateView):
    """Create a new Monte Carlo retirement scenario."""
    model = RetirementScenario
    form_class = MonteCarloScenarioForm
    template_name = 'jretirewise/scenario_monte_carlo_form.html'

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Set the current user as the owner."""
        form.instance.user = self.request.user
        messages.success(self.request, f'Monte Carlo scenario "{form.instance.name}" created successfully!')
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        """Redirect to scenario detail page."""
        return reverse_lazy('scenario-detail', kwargs={'pk': self.object.pk})


class MonteCarloScenarioUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing Monte Carlo scenario."""
    model = RetirementScenario
    form_class = MonteCarloScenarioForm
    template_name = 'jretirewise/scenario_monte_carlo_form.html'

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user, calculator_type='monte_carlo')

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-populate form with existing scenario parameters."""
        initial = super().get_initial()
        scenario = self.get_object()
        params = scenario.parameters or {}

        # Map stored parameters back to form fields
        if 'mode' in params:
            initial['calculation_mode'] = params['mode']
        if 'retirement_age' in params:
            initial['retirement_age'] = params['retirement_age']
        if 'life_expectancy' in params:
            initial['life_expectancy'] = params['life_expectancy']
        if 'portfolio_value' in params:
            initial['portfolio_value'] = params['portfolio_value']
        # Convert decimals back to percentages
        if 'annual_return_rate' in params:
            initial['expected_return'] = float(params['annual_return_rate']) * 100
        if 'inflation_rate' in params:
            initial['inflation_rate'] = float(params['inflation_rate']) * 100
        if 'return_std_dev' in params:
            initial['volatility'] = float(params['return_std_dev']) * 100
        if 'num_simulations' in params:
            initial['num_simulations'] = params['num_simulations']
        if 'target_success_rate' in params:
            initial['target_success_rate'] = int(params['target_success_rate'])
        if 'withdrawal_amount' in params:
            initial['withdrawal_amount'] = params['withdrawal_amount']
        if 'withdrawal_frequency' in params:
            initial['withdrawal_frequency'] = params['withdrawal_frequency']
        if 'social_security_start_age' in params:
            initial['social_security_start_age'] = params['social_security_start_age']
        if 'social_security_monthly' in params:
            initial['social_security_monthly'] = params['social_security_monthly']

        return initial

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Show success message."""
        messages.success(self.request, f'Monte Carlo scenario "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to scenario detail page."""
        return reverse_lazy('scenario-detail', kwargs={'pk': self.object.pk})


class BucketedWithdrawalScenarioCreateView(LoginRequiredMixin, CreateView):
    """Create a new bucketed withdrawal retirement scenario."""
    model = RetirementScenario
    form_class = BucketedWithdrawalScenarioForm
    template_name = 'jretirewise/scenario_bucketed_withdrawal_form.html'

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Set the current user as the owner."""
        form.instance.user = self.request.user
        messages.success(self.request, f'Bucketed withdrawal scenario "{form.instance.name}" created successfully!')
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        """Redirect to bucket management page."""
        return reverse_lazy('bucket-list', kwargs={'scenario_pk': self.object.pk})


class BucketedWithdrawalScenarioUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing bucketed withdrawal scenario."""
    model = RetirementScenario
    form_class = BucketedWithdrawalScenarioForm
    template_name = 'jretirewise/scenario_bucketed_withdrawal_form.html'

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user, calculator_type='bucketed_withdrawal')

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-populate form with existing scenario parameters."""
        initial = super().get_initial()
        scenario = self.get_object()
        params = scenario.parameters or {}

        # Map stored parameters back to form fields
        if 'retirement_age' in params:
            initial['retirement_age'] = params['retirement_age']
        if 'life_expectancy' in params:
            initial['life_expectancy'] = params['life_expectancy']
        if 'portfolio_value' in params:
            initial['portfolio_value'] = params['portfolio_value']
        # Convert decimals back to percentages
        if 'annual_return_rate' in params:
            initial['expected_return'] = float(params['annual_return_rate']) * 100
        if 'inflation_rate' in params:
            initial['inflation_rate'] = float(params['inflation_rate']) * 100

        return initial

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Show success message."""
        messages.success(self.request, f'Bucketed withdrawal scenario "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to bucket management page."""
        return reverse_lazy('bucket-list', kwargs={'scenario_pk': self.object.pk})


class BucketListView(LoginRequiredMixin, ListView):
    """List all withdrawal buckets for a scenario."""
    model = WithdrawalBucket
    template_name = 'jretirewise/bucket_list.html'
    context_object_name = 'buckets'
    paginate_by = 50

    def get_queryset(self):
        scenario_pk = self.kwargs['scenario_pk']
        scenario = get_object_or_404(
            RetirementScenario,
            pk=scenario_pk,
            user=self.request.user
        )
        return WithdrawalBucket.objects.filter(scenario=scenario).order_by('order', 'start_age')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scenario_pk = self.kwargs['scenario_pk']
        context['scenario'] = get_object_or_404(
            RetirementScenario,
            pk=scenario_pk,
            user=self.request.user
        )
        return context


class BucketCreateView(LoginRequiredMixin, CreateView):
    """Create a new withdrawal bucket for a scenario."""
    model = WithdrawalBucket
    form_class = WithdrawalBucketForm
    template_name = 'jretirewise/bucket_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scenario_pk = self.kwargs['scenario_pk']
        context['scenario'] = get_object_or_404(
            RetirementScenario,
            pk=scenario_pk,
            user=self.request.user
        )
        context['is_create'] = True
        return context

    def form_valid(self, form):
        scenario_pk = self.kwargs['scenario_pk']
        scenario = get_object_or_404(
            RetirementScenario,
            pk=scenario_pk,
            user=self.request.user
        )
        form.instance.scenario = scenario
        messages.success(self.request, f'Bucket "{form.instance.bucket_name}" created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bucket-list', kwargs={'scenario_pk': self.kwargs['scenario_pk']})


class BucketUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing withdrawal bucket."""
    model = WithdrawalBucket
    form_class = WithdrawalBucketForm
    template_name = 'jretirewise/bucket_form.html'

    def get_queryset(self):
        return WithdrawalBucket.objects.filter(scenario__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bucket = self.get_object()
        context['scenario'] = bucket.scenario
        context['is_create'] = False
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Bucket "{form.instance.bucket_name}" updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        bucket = self.get_object()
        return reverse_lazy('bucket-list', kwargs={'scenario_pk': bucket.scenario.pk})


class RunBucketedCalculationView(LoginRequiredMixin, View):
    """Run bucketed withdrawal calculation for a scenario."""

    def post(self, request, scenario_pk):
        """Handle POST request to run calculation."""
        import time
        from decimal import Decimal
        from jretirewise.calculations.calculators import DynamicBucketedWithdrawalCalculator
        from .models import CalculationResult, BucketedWithdrawalResult

        # Get scenario and verify ownership
        scenario = get_object_or_404(RetirementScenario, pk=scenario_pk, user=request.user)

        # Validate scenario has required parameters
        params = scenario.parameters
        if not all(k in params for k in ['portfolio_value', 'retirement_age', 'life_expectancy']):
            messages.error(request, 'Scenario missing required parameters: portfolio_value, retirement_age, life_expectancy')
            return redirect('bucket-list', scenario_pk=scenario_pk)

        # Get all withdrawal buckets for scenario
        buckets = scenario.withdrawal_buckets.all().order_by('order', 'start_age')
        if not buckets.exists():
            messages.error(request, 'Please add at least one withdrawal bucket before running the calculation.')
            return redirect('bucket-list', scenario_pk=scenario_pk)

        # Convert buckets to dictionaries for calculator
        bucket_dicts = []
        for bucket in buckets:
            bucket_dict = {
                'bucket_name': bucket.bucket_name,
                'start_age': bucket.start_age,
                'end_age': bucket.end_age,
                'target_withdrawal_rate': float(bucket.target_withdrawal_rate),
                'min_withdrawal_amount': float(bucket.min_withdrawal_amount) if bucket.min_withdrawal_amount else None,
                'max_withdrawal_amount': float(bucket.max_withdrawal_amount) if bucket.max_withdrawal_amount else None,
                'manual_withdrawal_override': float(bucket.manual_withdrawal_override) if bucket.manual_withdrawal_override else None,
                'expected_pension_income': float(bucket.expected_pension_income),
                'expected_social_security_income': float(bucket.expected_social_security_income),
                'healthcare_cost_adjustment': float(bucket.healthcare_cost_adjustment),
                'tax_loss_harvesting_enabled': bucket.tax_loss_harvesting_enabled,
                'roth_conversion_enabled': bucket.roth_conversion_enabled,
                'allowed_account_types': bucket.allowed_account_types or [],
                'prohibited_account_types': bucket.prohibited_account_types or [],
                'withdrawal_order': bucket.withdrawal_order or [],
            }
            bucket_dicts.append(bucket_dict)

        try:
            # Run calculation
            start_time = time.time()
            calculator = DynamicBucketedWithdrawalCalculator(
                portfolio_value=Decimal(str(params['portfolio_value'])),
                retirement_age=int(params['retirement_age']),
                life_expectancy=int(params['life_expectancy']),
                annual_return_rate=float(params.get('annual_return_rate', 0.07)),
                inflation_rate=float(params.get('inflation_rate', 0.03))
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

            # Create bucket lookup
            bucket_lookup = {b.bucket_name: b for b in buckets}

            for projection in result_data.get('projections', []):
                bucket_obj = bucket_lookup.get(projection.get('bucket_name'))
                if bucket_obj:
                    BucketedWithdrawalResult.objects.create(
                        calculation=calculation_result,
                        bucket=bucket_obj,
                        year=projection.get('year', 0),
                        age=projection.get('age', 0),
                        portfolio_value_start=Decimal(str(projection.get('portfolio_value_start', 0))),
                        portfolio_value_end=Decimal(str(projection.get('portfolio_value_end', 0))),
                        target_rate=float(projection.get('target_rate', 0)),
                        calculated_withdrawal=Decimal(str(projection.get('calculated_withdrawal', 0))),
                        actual_withdrawal=Decimal(str(projection.get('actual_withdrawal', 0))),
                        pension_income=Decimal(str(projection.get('pension_income', 0))),
                        social_security_income=Decimal(str(projection.get('social_security_income', 0))),
                        total_available_income=Decimal(str(projection.get('total_available_income', 0))),
                        investment_growth=Decimal(str(projection.get('investment_growth', 0))),
                    )

            messages.success(request, f'Calculation completed successfully in {execution_time_ms}ms!')
            return redirect('scenario-detail', pk=scenario_pk)

        except Exception as e:
            # Store error in result
            CalculationResult.objects.update_or_create(
                scenario=scenario,
                defaults={
                    'status': 'failed',
                    'result_data': {},
                    'error_message': str(e)
                }
            )
            messages.error(request, f'Calculation failed: {str(e)}')
            return redirect('bucket-list', scenario_pk=scenario_pk)


class BucketDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a withdrawal bucket."""
    model = WithdrawalBucket

    def get_queryset(self):
        return WithdrawalBucket.objects.filter(scenario__user=self.request.user)

    def delete(self, request, *args, **kwargs):
        bucket = self.get_object()
        bucket_name = bucket.bucket_name
        scenario_pk = bucket.scenario.pk
        messages.success(request, f'Bucket "{bucket_name}" deleted successfully!')
        response = super().delete(request, *args, **kwargs)
        self.success_url = reverse_lazy('bucket-list', kwargs={'scenario_pk': scenario_pk})
        return response

    def get_success_url(self):
        bucket = self.get_object()
        return reverse_lazy('bucket-list', kwargs={'scenario_pk': bucket.scenario.pk})


class HistoricalScenarioCreateView(LoginRequiredMixin, CreateView):
    """Create a new historical period analysis scenario."""
    model = RetirementScenario
    form_class = HistoricalScenarioForm
    template_name = 'jretirewise/scenario_historical_form.html'

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Set the current user as the owner."""
        form.instance.user = self.request.user
        messages.success(self.request, f'Historical analysis scenario "{form.instance.name}" created successfully!')
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        """Redirect to scenario detail page."""
        return reverse_lazy('scenario-detail', kwargs={'pk': self.object.pk})


class HistoricalScenarioUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing historical analysis scenario."""
    model = RetirementScenario
    form_class = HistoricalScenarioForm
    template_name = 'jretirewise/scenario_historical_form.html'

    def get_queryset(self):
        return RetirementScenario.objects.filter(user=self.request.user, calculator_type='historical')

    def get_form_kwargs(self):
        """Pass user to form for pre-filling values."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-populate form with existing scenario parameters."""
        initial = super().get_initial()
        scenario = self.get_object()
        params = scenario.parameters or {}

        # Map stored parameters back to form fields
        if 'retirement_age' in params:
            initial['retirement_age'] = params['retirement_age']
        if 'life_expectancy' in params:
            initial['life_expectancy'] = params['life_expectancy']
        if 'portfolio_value' in params:
            initial['portfolio_value'] = params['portfolio_value']
        # Convert decimals back to percentages
        if 'withdrawal_rate' in params:
            initial['withdrawal_rate'] = float(params['withdrawal_rate']) * 100
        if 'stock_allocation' in params:
            initial['stock_allocation'] = int(float(params['stock_allocation']) * 100)
        if 'social_security_start_age' in params:
            initial['social_security_start_age'] = params['social_security_start_age']
        if 'social_security_annual' in params:
            initial['social_security_annual'] = params['social_security_annual']
        if 'pension_annual' in params:
            initial['pension_annual'] = params['pension_annual']

        return initial

    def get_context_data(self, **kwargs):
        """Add prefilled fields info to context."""
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form and hasattr(form, 'get_prefilled_fields'):
            context['prefilled_fields'] = form.get_prefilled_fields()
        return context

    def form_valid(self, form):
        """Show success message."""
        messages.success(self.request, f'Historical analysis scenario "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to scenario detail page."""
        return reverse_lazy('scenario-detail', kwargs={'pk': self.object.pk})


class RunHistoricalCalculationView(LoginRequiredMixin, View):
    """Run historical period analysis calculation for a scenario."""

    def post(self, request, pk):
        """Handle POST request to run calculation."""
        import time
        from jretirewise.calculations.calculators import HistoricalPeriodCalculator

        # Get scenario and verify ownership
        scenario = get_object_or_404(RetirementScenario, pk=pk, user=request.user)

        # Validate scenario has required parameters
        params = scenario.parameters
        if not all(k in params for k in ['portfolio_value', 'retirement_age', 'life_expectancy']):
            messages.error(request, 'Scenario missing required parameters: portfolio_value, retirement_age, life_expectancy')
            return redirect('scenario-detail', pk=pk)

        try:
            # Run calculation
            start_time = time.time()
            calculator = HistoricalPeriodCalculator(
                portfolio_value=float(params['portfolio_value']),
                retirement_age=int(params['retirement_age']),
                life_expectancy=int(params['life_expectancy']),
                withdrawal_rate=float(params.get('withdrawal_rate', 0.04)),
                stock_allocation=float(params.get('stock_allocation', 0.60)),
                social_security_start_age=params.get('social_security_start_age'),
                social_security_annual=float(params.get('social_security_annual', 0)),
                pension_annual=float(params.get('pension_annual', 0)),
            )
            result_data = calculator.calculate()
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Store result in database
            CalculationResult.objects.update_or_create(
                scenario=scenario,
                defaults={
                    'status': 'completed',
                    'result_data': result_data,
                    'execution_time_ms': execution_time_ms,
                    'error_message': ''
                }
            )

            messages.success(request, f'Historical analysis completed in {execution_time_ms}ms! Tested {result_data.get("total_periods_tested", 0)} historical periods.')
            return redirect('scenario-detail', pk=pk)

        except Exception as e:
            logger.exception(f"Historical calculation failed for scenario {pk}")
            # Store error in result
            CalculationResult.objects.update_or_create(
                scenario=scenario,
                defaults={
                    'status': 'failed',
                    'result_data': {},
                    'error_message': str(e)
                }
            )
            messages.error(request, f'Calculation failed: {str(e)}')
            return redirect('scenario-detail', pk=pk)
