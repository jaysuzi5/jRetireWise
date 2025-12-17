# Historical Market Data

This directory contains historical market return data used for backtesting retirement scenarios against actual market performance.

## Data Sources

### Primary Source
- **NYU Stern (Aswath Damodaran)**: [Historical Returns on Stocks, Bonds and Bills: 1928-2024](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)

### Supporting Sources
- **FRED (Federal Reserve Economic Data)**: [10-Year Treasury Constant Maturity Rate](https://fred.stlouisfed.org/series/DGS10)
- **Bureau of Labor Statistics**: CPI Inflation Data
- **Ibbotson SBBI (Stocks, Bonds, Bills, and Inflation)**: The gold standard for historical returns, now maintained by Morningstar. Available via [CFA Institute Research Foundation](https://rpc.cfainstitute.org/research/foundation/1982/rf-v1982-sbbi-past-and-future)

## Data Included

| Dataset | Description | Time Period |
|---------|-------------|-------------|
| `SP500_RETURNS` | S&P 500 Total Returns (including dividends) | 1960-2024 |
| `BOND_RETURNS` | 10-Year US Treasury Total Returns | 1960-2024 |
| `INFLATION_RATES` | Annual CPI Inflation Rates | 1960-2024 |

## Why Total Return (Not Just Yield)?

**This data uses Total Return for bonds, which is the correct approach for retirement backtesting.**

### Total Return = Yield + Price Change

When you hold bonds (either directly or in a fund), you receive:
1. **Coupon/Interest payments** (the yield)
2. **Capital gains or losses** (price changes as interest rates move)

### Example: Why This Matters

| Year | Approximate Yield | Price Change | Total Return |
|------|-------------------|--------------|--------------|
| 1982 | ~10-14% | +18-20% | **+32.81%** |
| 2022 | ~2-4% | -18% | **-17.46%** |

**1982 Context**: Fed Chair Paul Volcker had raised rates to nearly 20% to fight inflation. The 10-year Treasury yield peaked at over 15% in late 1981. When rates began falling in 1982, bond prices soared, resulting in one of the best years ever for bonds.

**2022 Context**: Rates spiked from near-zero to over 4%, causing massive bond price declines despite continued coupon payments.

### Real-World Portfolio Behavior

- Most retirees hold bond funds/ETFs, not individual bonds held to maturity
- Fund NAV reflects both yield AND price changes
- Total return accurately represents actual portfolio performance
- Using just yield would hide significant gains (1982) or losses (2022)

## Historical Context: Notable Periods

### High Bond Return Years
- **1982**: 32.81% - Rates fell sharply as Volcker's inflation fight succeeded
- **1985**: 25.71% - Continued rate decline
- **1995**: 23.48% - Mid-90s rate environment
- **2008**: 20.22% - Flight to safety during financial crisis

### Negative Bond Return Years
- **2022**: -17.46% - Fastest rate hikes in decades
- **2009**: -11.12% - Post-crisis rate normalization
- **1994**: -8.04% - Unexpected Fed tightening
- **2013**: -7.91% - "Taper tantrum"

### High Inflation Periods
- **1979-1981**: 13.3%, 12.4%, 8.9% - Peak stagflation era
- **1974**: 12.2% - Oil crisis inflation
- **2021-2022**: 7.0%, 6.5% - Post-COVID inflation

## Data Accuracy Notes

1. **S&P 500 Returns**: Total returns including reinvested dividends, not price-only returns
2. **Bond Returns**: 10-Year Treasury total returns, reflecting both coupon income and price changes
3. **Inflation**: Annual average CPI-U (Consumer Price Index for All Urban Consumers)
4. **2024 Data**: Estimated based on year-to-date performance; will be updated when final data available

## Usage in Retirement Calculations

The Historical Period Calculator uses this data to:

1. **Test retirement scenarios** against every possible starting year (1960-present)
2. **Calculate blended returns** based on user's stock/bond allocation
3. **Apply actual inflation** to withdrawal amounts (inflation-adjusted withdrawals)
4. **Identify vulnerable periods** where a retirement strategy would have failed
5. **Show best/worst/median cases** based on actual historical outcomes

### Blended Return Calculation

```python
blended_return = (stock_return * stock_allocation) + (bond_return * (1 - stock_allocation))
```

For example, with 60% stocks / 40% bonds in 1982:
- S&P 500: 21.41%
- Bonds: 32.81%
- Blended: (0.2141 × 0.60) + (0.3281 × 0.40) = **26.0%**

## Updating the Data

When new annual data becomes available:

1. Update `SP500_RETURNS` with the new year's S&P 500 total return
2. Update `BOND_RETURNS` with the new year's 10-Year Treasury total return
3. Update `INFLATION_RATES` with the new year's CPI inflation rate
4. Update the "2024 Data" note above if applicable

Data is typically finalized in January/February for the previous calendar year.

## References

- Damodaran, A. "Historical Returns on Stocks, Bonds and Bills." NYU Stern School of Business.
- Ibbotson, R. G., & Sinquefield, R. A. "Stocks, Bonds, Bills, and Inflation." CFA Institute Research Foundation.
- Federal Reserve Bank of St. Louis. "FRED Economic Data."
- U.S. Bureau of Labor Statistics. "Consumer Price Index."
