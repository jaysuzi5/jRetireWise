"""
Scenario and calculation result models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class RetirementScenario(models.Model):
    """A retirement scenario with specific parameters."""

    CALCULATOR_TYPES = [
        ('4_percent', '4% Rule'),
        ('4_7_percent', '4.7% Rule'),
        ('monte_carlo', 'Monte Carlo'),
        ('historical', 'Historical Analysis'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    calculator_type = models.CharField(max_length=50, choices=CALCULATOR_TYPES)

    # Scenario parameters stored as JSON
    parameters = models.JSONField(default=dict)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scenario'
        verbose_name = 'Retirement Scenario'
        verbose_name_plural = 'Retirement Scenarios'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['calculator_type']),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.calculator_type})"


class CalculationResult(models.Model):
    """Results from a calculation."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    scenario = models.OneToOneField(
        RetirementScenario,
        on_delete=models.CASCADE,
        related_name='result'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Result data as JSON
    result_data = models.JSONField(default=dict)

    # Execution metrics
    execution_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calculation_result'
        verbose_name = 'Calculation Result'
        verbose_name_plural = 'Calculation Results'
        indexes = [
            models.Index(fields=['scenario']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Result for {self.scenario.name} ({self.status})"
