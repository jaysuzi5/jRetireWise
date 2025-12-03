# jRetireWise

**Professional retirement planning calculator** that empowers users to model their retirement scenarios with confidence. jRetireWise provides deterministic and stochastic calculation engines to help answer the critical question: "Will my money last?"

## Features

- **Financial Profile Management**: Track your assets, income, and spending needs
- **Multiple Calculation Methods**: Choose from 4% rule, 4.7% rule, and advanced simulation methods
- **Scenario Planning**: Create and compare different retirement scenarios
- **Visual Projections**: Interactive charts showing portfolio projections over time
- **Google OAuth Integration**: Secure authentication with your Google account
- **Cloud-Native**: Deployed on Kubernetes with full CI/CD automation

## Retirement Calculation Methods

### The 4% Rule

**Conservative Approach for Reliable Retirement Income**

The 4% rule is based on the Trinity Study (1998), which analyzed historical market returns and withdrawal rates. The rule states that you can withdraw 4% of your initial portfolio value in your first year of retirement, then adjust that amount for inflation in subsequent years.

#### How It Works

1. **Calculate Initial Withdrawal**: Portfolio Value × 0.04
2. **Apply Withdrawals**: Each year, withdraw the adjusted amount (previous year's withdrawal × inflation multiplier)
3. **Calculate Returns**: Remaining portfolio earns the expected annual return
4. **Assess Sustainability**: Check if the portfolio lasts through retirement

#### Example

- Portfolio: $1,000,000
- Initial Withdrawal (Year 1): $1,000,000 × 0.04 = **$40,000**
- Year 2 (3% inflation): $40,000 × 1.03 = **$41,200**
- Year 3 (3% inflation): $41,200 × 1.03 = **$42,436**
- And so on...

#### Strengths

- ✅ Historically successful (92% success rate across historical periods)
- ✅ Conservative and reliable
- ✅ Recommended for risk-averse retirees
- ✅ Works well with 60/40 stock/bond portfolios

#### Considerations

- 💡 May be overly conservative if you have other income sources
- 💡 Fixed withdrawal may feel inflexible in market downturns
- 💡 Assumes stable inflation and market returns

**Reference**: Trinity Study - "A Retrospective Look at the Viability of the 4 Percent Rule"

---

### The 4.7% Rule

**Balanced Approach for Modern Retirees**

The 4.7% rule is a more aggressive variant that emerged from research by analysts seeking to provide higher retirement income while still maintaining reasonable success rates. It's suitable for retirees who have flexibility in their spending and can adjust withdrawals when market conditions warrant it.

#### How It Works

The calculation is identical to the 4% rule, but uses a slightly higher initial withdrawal percentage:

1. **Calculate Initial Withdrawal**: Portfolio Value × 0.047
2. **Apply Withdrawals**: Adjust subsequent years by inflation (same as 4% rule)
3. **Calculate Returns**: Remaining portfolio earns expected returns
4. **Monitor Flexibility**: Consider adjusting withdrawals in down markets

#### Example

- Portfolio: $1,000,000
- Initial Withdrawal (Year 1): $1,000,000 × 0.047 = **$47,000**
- Year 2 (3% inflation): $47,000 × 1.03 = **$48,410**
- Year 3 (3% inflation): $48,410 × 1.03 = **$49,862**
- And so on...

#### Strengths

- ✅ Provides approximately 7% more income than 4% rule
- ✅ Still maintains strong historical success rates (~88-90%)
- ✅ Good for those wanting more lifestyle flexibility
- ✅ Better reflects modern portfolio construction

#### Considerations

- 💡 Requires flexibility to reduce withdrawals in poor market years
- 💡 Higher risk of portfolio depletion vs. 4% rule
- 💡 Requires active monitoring of market performance
- 💡 Better suited for those with other income sources

---

### Projection Metrics

Both calculation methods provide these key metrics:

- **Success Rate**: Percentage of historical periods where the portfolio never depleted
- **Final Portfolio Value**: Ending balance at life expectancy
- **Yearly Withdrawals**: Amount available to spend each year
- **Portfolio Balance**: Remaining portfolio value at any given year

### How to Use jRetireWise

1. **Create Your Financial Profile**: Enter your current age, retirement age, life expectancy, portfolio value, and annual spending needs
2. **Select a Scenario**: Choose a calculation method (4% rule or 4.7% rule)
3. **Review Projections**: Examine the year-by-year projection of your portfolio
4. **Adjust Parameters**: Try different spending levels, return rates, or inflation rates to stress-test your plan
5. **Compare Scenarios**: Create multiple scenarios to find the right balance between income and security

---

## Technology Stack

- **Backend**: Python 3.11+ with Django 5.0+
- **Frontend**: Django templates with Tailwind CSS and Chart.js
- **Database**: PostgreSQL 14+
- **Infrastructure**: Docker and Kubernetes
- **CI/CD**: GitHub Actions with ArgoCD

## Documentation

- **Development Guide**: See [CLAUDE.md](CLAUDE.md) for setup, testing, and deployment instructions
- **Project Roadmap**: See [documents/plan.md](documents/plan.md) for the complete project roadmap and phase planning