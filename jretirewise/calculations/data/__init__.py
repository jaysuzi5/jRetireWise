"""Historical data for retirement calculations."""

from .historical_returns import (
    SP500_RETURNS,
    BOND_RETURNS,
    INFLATION_RATES,
    NOTABLE_PERIODS,
    get_returns_for_period,
    get_inflation_for_period,
    get_available_start_years,
)

__all__ = [
    'SP500_RETURNS',
    'BOND_RETURNS',
    'INFLATION_RATES',
    'NOTABLE_PERIODS',
    'get_returns_for_period',
    'get_inflation_for_period',
    'get_available_start_years',
]
