"""Custom template filters for jRetireWise."""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply the value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide the value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def to_percentage(value):
    """Convert decimal (0.07) to percentage (7.0)."""
    try:
        return float(value) * 100
    except (ValueError, TypeError):
        return 0
