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


@register.filter
def as_percentage(value):
    """
    Smartly convert value to percentage for display.

    If value < 1, treat as decimal and multiply by 100 (e.g., 0.07 -> 7.0)
    If value >= 1, assume it's already a percentage (e.g., 7.0 -> 7.0)

    This handles both old data (stored as decimal) and new data (stored as percentage).
    """
    try:
        val = float(value)
        if val < 1:
            return val * 100
        return val
    except (ValueError, TypeError):
        return 0
