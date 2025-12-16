"""
Historical market return data for backtesting retirement scenarios.

Data sources:
- S&P 500 total returns (including dividends reinvested)
- US Treasury Bond returns (10-year)
- Inflation rates (CPI)

All values are expressed as decimals (e.g., 0.15 = 15% return)
"""

# S&P 500 Total Returns (including dividends) by year
# Source: Historical S&P 500 data, publicly available
SP500_RETURNS = {
    1960: 0.0047,
    1961: 0.2689,
    1962: -0.0873,
    1963: 0.2280,
    1964: 0.1648,
    1965: 0.1245,
    1966: -0.1006,
    1967: 0.2398,
    1968: 0.1106,
    1969: -0.0850,
    1970: 0.0401,
    1971: 0.1431,
    1972: 0.1898,
    1973: -0.1466,
    1974: -0.2647,
    1975: 0.3720,
    1976: 0.2384,
    1977: -0.0718,
    1978: 0.0656,
    1979: 0.1844,
    1980: 0.3242,
    1981: -0.0491,
    1982: 0.2141,
    1983: 0.2251,
    1984: 0.0627,
    1985: 0.3216,
    1986: 0.1847,
    1987: 0.0581,
    1988: 0.1681,
    1989: 0.3149,
    1990: -0.0306,
    1991: 0.3055,
    1992: 0.0762,
    1993: 0.1008,
    1994: 0.0132,
    1995: 0.3758,
    1996: 0.2296,
    1997: 0.3336,
    1998: 0.2858,
    1999: 0.2104,
    2000: -0.0910,
    2001: -0.1189,
    2002: -0.2210,
    2003: 0.2869,
    2004: 0.1088,
    2005: 0.0491,
    2006: 0.1579,
    2007: 0.0549,
    2008: -0.3700,
    2009: 0.2646,
    2010: 0.1506,
    2011: 0.0211,
    2012: 0.1600,
    2013: 0.3239,
    2014: 0.1369,
    2015: 0.0138,
    2016: 0.1196,
    2017: 0.2183,
    2018: -0.0438,
    2019: 0.3149,
    2020: 0.1840,
    2021: 0.2871,
    2022: -0.1811,
    2023: 0.2629,
    2024: 0.2500,  # Estimated through end of year
}

# 10-Year US Treasury Bond Returns by year
BOND_RETURNS = {
    1960: 0.1178,
    1961: 0.0206,
    1962: 0.0569,
    1963: 0.0183,
    1964: 0.0351,
    1965: 0.0071,
    1966: 0.0465,
    1967: -0.0192,
    1968: 0.0426,
    1969: -0.0508,
    1970: 0.1686,
    1971: 0.0926,
    1972: 0.0268,
    1973: 0.0311,
    1974: 0.0535,
    1975: 0.0361,
    1976: 0.1575,
    1977: 0.0129,
    1978: -0.0007,
    1979: 0.0186,
    1980: 0.0395,
    1981: 0.0861,
    1982: 0.3291,
    1983: 0.0341,
    1984: 0.1543,
    1985: 0.2571,
    1986: 0.1946,
    1987: -0.0296,
    1988: 0.0822,
    1989: 0.1768,
    1990: 0.0618,
    1991: 0.1530,
    1992: 0.0934,
    1993: 0.1421,
    1994: -0.0804,
    1995: 0.2348,
    1996: 0.0130,
    1997: 0.0993,
    1998: 0.1492,
    1999: -0.0782,
    2000: 0.1666,
    2001: 0.0557,
    2002: 0.1526,
    2003: 0.0138,
    2004: 0.0449,
    2005: 0.0287,
    2006: 0.0196,
    2007: 0.0966,
    2008: 0.2022,
    2009: -0.1112,
    2010: 0.0841,
    2011: 0.1612,
    2012: 0.0297,
    2013: -0.0791,
    2014: 0.1075,
    2015: 0.0139,
    2016: 0.0069,
    2017: 0.0217,
    2018: 0.0028,
    2019: 0.0892,
    2020: 0.1126,
    2021: -0.0426,
    2022: -0.1746,
    2023: 0.0396,
    2024: 0.0200,  # Estimated
}

# Annual Inflation Rates (CPI) by year
INFLATION_RATES = {
    1960: 0.0172,
    1961: 0.0067,
    1962: 0.0122,
    1963: 0.0165,
    1964: 0.0092,
    1965: 0.0192,
    1966: 0.0335,
    1967: 0.0304,
    1968: 0.0472,
    1969: 0.0611,
    1970: 0.0549,
    1971: 0.0336,
    1972: 0.0341,
    1973: 0.0880,
    1974: 0.1218,
    1975: 0.0694,
    1976: 0.0486,
    1977: 0.0670,
    1978: 0.0903,
    1979: 0.1331,
    1980: 0.1240,
    1981: 0.0894,
    1982: 0.0387,
    1983: 0.0380,
    1984: 0.0395,
    1985: 0.0377,
    1986: 0.0113,
    1987: 0.0441,
    1988: 0.0442,
    1989: 0.0465,
    1990: 0.0610,
    1991: 0.0306,
    1992: 0.0290,
    1993: 0.0275,
    1994: 0.0267,
    1995: 0.0254,
    1996: 0.0332,
    1997: 0.0177,
    1998: 0.0161,
    1999: 0.0268,
    2000: 0.0339,
    2001: 0.0155,
    2002: 0.0238,
    2003: 0.0188,
    2004: 0.0326,
    2005: 0.0342,
    2006: 0.0254,
    2007: 0.0408,
    2008: 0.0009,
    2009: 0.0272,
    2010: 0.0150,
    2011: 0.0296,
    2012: 0.0174,
    2013: 0.0150,
    2014: 0.0076,
    2015: 0.0073,
    2016: 0.0212,
    2017: 0.0213,
    2018: 0.0191,
    2019: 0.0231,
    2020: 0.0123,
    2021: 0.0700,
    2022: 0.0650,
    2023: 0.0340,
    2024: 0.0290,  # Estimated
}


def get_returns_for_period(start_year: int, num_years: int,
                           stock_allocation: float = 0.6) -> list:
    """
    Get blended portfolio returns for a specific historical period.

    Args:
        start_year: Starting year of the period
        num_years: Number of years needed
        stock_allocation: Percentage in stocks (remainder in bonds)

    Returns:
        List of annual returns for the period
    """
    returns = []
    bond_allocation = 1.0 - stock_allocation

    for i in range(num_years):
        year = start_year + i
        if year in SP500_RETURNS and year in BOND_RETURNS:
            blended = (SP500_RETURNS[year] * stock_allocation +
                       BOND_RETURNS[year] * bond_allocation)
            returns.append(blended)
        else:
            # If we run out of data, use average historical returns
            avg_stock = sum(SP500_RETURNS.values()) / len(SP500_RETURNS)
            avg_bond = sum(BOND_RETURNS.values()) / len(BOND_RETURNS)
            blended = avg_stock * stock_allocation + avg_bond * bond_allocation
            returns.append(blended)

    return returns


def get_inflation_for_period(start_year: int, num_years: int) -> list:
    """
    Get inflation rates for a specific historical period.

    Args:
        start_year: Starting year of the period
        num_years: Number of years needed

    Returns:
        List of annual inflation rates for the period
    """
    rates = []

    for i in range(num_years):
        year = start_year + i
        if year in INFLATION_RATES:
            rates.append(INFLATION_RATES[year])
        else:
            # Use average if data not available
            avg_inflation = sum(INFLATION_RATES.values()) / len(INFLATION_RATES)
            rates.append(avg_inflation)

    return rates


def get_available_start_years(num_years_needed: int) -> list:
    """
    Get list of years that can be used as starting points for backtesting.

    Args:
        num_years_needed: Number of years of data required

    Returns:
        List of valid starting years
    """
    min_year = min(SP500_RETURNS.keys())
    max_year = max(SP500_RETURNS.keys())

    # We need num_years_needed years of data from the start year
    valid_years = []
    for year in range(min_year, max_year - num_years_needed + 2):
        valid_years.append(year)

    return valid_years


# Notable historical periods for analysis
NOTABLE_PERIODS = {
    'stagflation_1970s': {
        'start_year': 1973,
        'end_year': 1982,
        'description': 'High inflation and poor market returns',
    },
    'black_monday_1987': {
        'start_year': 1987,
        'end_year': 1987,
        'description': 'Single-day market crash of 22%',
    },
    'dot_com_bust': {
        'start_year': 2000,
        'end_year': 2002,
        'description': 'Tech bubble burst, 3 years of negative returns',
    },
    'great_financial_crisis': {
        'start_year': 2007,
        'end_year': 2009,
        'description': 'Housing crisis and market collapse',
    },
    'lost_decade': {
        'start_year': 2000,
        'end_year': 2009,
        'description': 'Decade of minimal stock market returns',
    },
    'covid_crash': {
        'start_year': 2020,
        'end_year': 2020,
        'description': 'Rapid crash and recovery',
    },
    'bull_market_1990s': {
        'start_year': 1995,
        'end_year': 1999,
        'description': 'Historic bull market run',
    },
    'post_gfc_recovery': {
        'start_year': 2009,
        'end_year': 2019,
        'description': 'Extended bull market after crisis',
    },
}
