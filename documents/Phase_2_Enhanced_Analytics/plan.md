# Phase 2: Enhanced Analytics & Sophisticated Calculations - 6-8 weeks

**Goal**: Add advanced portfolio management, dynamic withdrawal strategies, Monte Carlo simulations, historical analysis, and advanced visualization.

**Status**: Planned for implementation after Phase 1 MVP completion.

---

## 2.0 Advanced Portfolio Management (NEW - First Priority)

**Goal**: Build comprehensive multi-account portfolio tracking with flexible account types, growth rate management, and historical valuation tracking.

This is the foundational work that enables all subsequent Phase 2 calculations. The portfolio system must support complex retirement scenarios with multiple account types and flexible growth rates.

### 2.0.1 Multi-Account Portfolio System

#### Account Types Support
- **Retirement Accounts**:
  - Traditional 401(k)
  - Roth 401(k)
  - Traditional IRA
  - Roth IRA
  - SEP IRA
  - Solo 401(k)
  - Backdoor Roth capability

- **Investment Accounts**:
  - Taxable Brokerage
  - Joint Investment Account
  - Partnership Account

- **Savings Accounts**:
  - Regular Savings Account
  - High-Yield Savings Account (HYSA)
  - Money Market Account

- **Health-Related**:
  - Health Savings Account (HSA)
  - Medical Savings Account (MSA)

- **Other**:
  - College 529 Plans
  - Certificates of Deposit (CDs)
  - Treasury Securities
  - Bonds
  - Custom Account Type

#### Account Properties
Each account must support the following properties:

- **Basic Information**:
  - Account Name (user-friendly identifier)
  - Account Type (from list above)
  - Account Number/Reference (optional, for tracking)
  - Description/Notes (free-form text field)
  - Institution Name (where account is held)

- **Financial Data**:
  - Current Value (balance as of date)
  - Default Growth Rate (annual % return, used in scenarios)
  - Inflation Adjustment (optional, applied to growth rate)
  - Expected Contribution Rate (annual additions, if any)
  - Investment Allocation (percentage in stocks/bonds/other for risk modeling)

- **Withdrawal Rules** (for calculations):
  - Withdrawal Priority (order to withdraw from this account)
  - Withdrawal Restrictions (min age, penalty-free date)
  - Tax Treatment (pre-tax, post-tax, tax-exempt)
  - Required Minimum Distribution (RMD) age and percentage

- **Metadata**:
  - Created Date
  - Last Updated Date
  - Status (Active, Closed, Merged)
  - Data Source (manual entry, imported, API sync)

#### Portfolio Dashboard
- **Summary View**:
  - Total Portfolio Value
  - Breakdown by account type (pie/donut chart)
  - Total contributions and withdrawals (YTD)
  - Weighted average growth rate
  - Estimated portfolio value at retirement

- **Account List View**:
  - Table of all accounts with key metrics
  - Sort/filter by account type, institution, date
  - Color-coded status indicators
  - Quick-edit inline capability

- **Performance Tracking**:
  - Portfolio total vs benchmark comparison
  - Account-level performance metrics
  - Growth rate vs default rate comparison

### 2.0.2 Portfolio Value History Tracking

#### Historical Snapshots
- **Automatic History Recording**:
  - When user updates current value, automatically save snapshot
  - Store: Account ID, value, date, timestamp, user
  - Allow manual snapshot entry for retroactive data
  - Support bulk historical data import (CSV)

- **History Retention**:
  - Keep complete history (no deletion, only archiving)
  - Timeline view: graph portfolio growth over time
  - Period comparison: select date ranges and compare growth
  - Export historical data to CSV or Excel

#### Historical Analysis
- **Value Trends**:
  - Growth trajectory visualization (Chart.js)
  - Period-over-period growth rates (YoY, QoQ)
  - Contribution vs growth breakdown (stacked area chart)
  - Projected future value based on historical trends

- **Valuation Milestones**:
  - Track when portfolio reached certain values
  - Goal progress indicator (% of retirement target)
  - Years to reach retirement goal (based on growth rate)

#### Data Integrity
- **Audit Trail**:
  - Log all value changes with user/source/timestamp
  - Allow restoration of previous snapshots
  - Mark imported vs manually entered data
  - Data reconciliation reports (detect anomalies)

### 2.0.3 Database Schema & Models

#### Core Models
```
Portfolio:
  - user (FK)
  - name
  - description
  - created_date
  - updated_date

Account:
  - portfolio (FK)
  - account_type (CharField: choices)
  - account_name
  - account_number (optional)
  - institution_name
  - description
  - current_value (Decimal)
  - default_growth_rate (Float, %)
  - inflation_adjustment (Float, %)
  - expected_contribution_rate (Float, %)
  - investment_allocation (JSON: stocks%, bonds%, other%)
  - withdrawal_priority (Integer)
  - withdrawal_restrictions (JSON)
  - tax_treatment (CharField: pre-tax/post-tax/tax-exempt)
  - rmd_age (Integer)
  - rmd_percentage (Float)
  - status (CharField: active/closed/merged)
  - created_date
  - updated_date
  - data_source (CharField: manual/import/api)

AccountValueHistory:
  - account (FK)
  - value (Decimal)
  - recorded_date
  - recorded_timestamp
  - user (FK, who recorded this)
  - source (CharField: manual/import/system)
  - notes (optional)

PortfolioSnapshot:
  - portfolio (FK)
  - total_value (Decimal)
  - snapshot_date
  - created_timestamp
  - calculated_from (CharField: all_accounts/last_snapshot)
  - notes (optional)
```

### 2.0.4 API Endpoints

#### Portfolio Management
- `POST /api/v1/portfolios/` - Create portfolio
- `GET /api/v1/portfolios/` - List user's portfolios
- `GET /api/v1/portfolios/{id}/` - Get portfolio details
- `PUT /api/v1/portfolios/{id}/` - Update portfolio
- `DELETE /api/v1/portfolios/{id}/` - Delete portfolio

#### Account Management
- `POST /api/v1/accounts/` - Create account
- `GET /api/v1/accounts/` - List accounts in portfolio
- `GET /api/v1/accounts/{id}/` - Get account details
- `PUT /api/v1/accounts/{id}/` - Update account
- `PATCH /api/v1/accounts/{id}/` - Partial update (e.g., just value)
- `DELETE /api/v1/accounts/{id}/` - Delete account

#### Historical Data
- `POST /api/v1/accounts/{id}/history/` - Record value snapshot
- `GET /api/v1/accounts/{id}/history/` - Get account history
- `GET /api/v1/accounts/{id}/history/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Date-range query
- `POST /api/v1/accounts/{id}/history/import/` - Bulk import CSV
- `GET /api/v1/accounts/{id}/history/export/` - Export to CSV

#### Portfolio Snapshots
- `POST /api/v1/portfolios/{id}/snapshots/` - Create full portfolio snapshot
- `GET /api/v1/portfolios/{id}/snapshots/` - List portfolio snapshots
- `GET /api/v1/portfolios/{id}/snapshots/{snapshot_id}/` - Get snapshot details

### 2.0.5 Frontend - Portfolio Management UI

#### Pages to Build
- **Portfolio Dashboard** (main overview page)
  - Total portfolio value with trend chart
  - Account breakdown visualization
  - Quick-add account button
  - Recent transactions/changes

- **Accounts List** (manage individual accounts)
  - Table of all accounts
  - Filter by type, institution, status
  - Sort by value, growth rate, date
  - Inline edit capability
  - Quick-delete with confirmation

- **Account Detail** (create/edit form)
  - Form with account type dropdown
  - All properties as form fields
  - Validation (required fields, numeric constraints)
  - Default values based on account type
  - Save/cancel buttons

- **History Viewer** (analyze account growth)
  - Timeline graph of value over time
  - Date range selector
  - Comparison view (account vs portfolio)
  - Export buttons (CSV, PDF)
  - Growth statistics (min, max, avg, std dev)

- **Portfolio Settings**
  - Manage multiple portfolios
  - Default growth rates by account type
  - Risk allocation profiles
  - Historical data import tool

#### Components
- **AccountForm** (Reusable account add/edit form)
- **HistoryChart** (Chart.js visualization of account history)
- **PortfolioSummary** (Dashboard widget)
- **AccountTable** (Filterable, sortable account list)
- **ValueHistoryTimeline** (Date range picker + chart)

### 2.0.6 Testing Requirements

- **Unit Tests**:
  - Account model validation (type, growth rate ranges)
  - Portfolio calculations (total value, weighted average)
  - History snapshot creation and retrieval
  - Growth rate application to projections

- **Integration Tests**:
  - Create portfolio → add accounts → record history
  - Bulk import CSV and verify accuracy
  - Account type-specific validations
  - Permission checks (user can only see own portfolios)

- **API Tests**:
  - CRUD operations for portfolios and accounts
  - Date-range history queries
  - Export functionality
  - Error handling (invalid account types, negative values)

### 2.0.7 Deliverables for 2.0

- Multi-account portfolio system with 10+ account types
- Account value history tracking with automatic snapshots
- Complete CRUD API endpoints
- Portfolio dashboard with summary views
- History visualization and export
- Comprehensive test coverage (unit, integration, API)
- Database migrations
- Frontend portfolio management UI

---

## 2.1 Advanced Calculation Engines (Updated for Complex Portfolio)

**Goal**: Implement sophisticated retirement calculators that leverage the advanced portfolio system.

**Note**: Phase 2.0 (Advanced Portfolio) must be completed first, as all calculations depend on the multi-account portfolio structure.

### 2.1.1 Reworked Basic Calculators with Portfolio Support

#### Enhanced 4% Rule Calculator
- **Portfolio Integration**:
  - Accept complex portfolio (multiple accounts of different types)
  - Consider account-specific withdrawal restrictions
  - Apply tax-aware withdrawal sequencing

- **Withdrawal Logic**:
  - Calculate 4% of starting portfolio value
  - Track annual withdrawals from each account type
  - Account for RMD (Required Minimum Distribution) timing
  - Flag tax-inefficient withdrawals

- **Output**:
  - Annual breakdown (portfolio value, withdrawal amount, remaining balance)
  - Account-by-account withdrawal plan
  - Tax impact summary
  - Warning flags (RMD misses, early access penalties)

#### Enhanced 4.7% Rule Calculator
- Similar to 4% but with higher withdrawal rate
- Account-specific constraints
- Sustainability analysis (how long portfolio lasts)
- Success probability (simplified based on historical returns)

### 2.1.2 Dynamic Bucketed Withdrawal Rate Calculator (NEW)

**Goal**: Allow flexible withdrawal rates that change based on age/time periods (buckets).

This calculator supports complex retirement scenarios where withdrawal strategies change over different life phases.

#### Concept
Instead of a single fixed withdrawal rate, allow multiple "buckets" where each bucket defines:
- **Time Period** (age range or retirement year range)
- **Withdrawal Rate** (% of portfolio for that period)
- **Constraints** (accounts that can be used, restrictions)

#### Example Scenario
```
Bucket 1: Ages 55-59.5 (Pre-retirement buffer)
  - Target withdrawal rate: 2% (conservative)
  - Can only use: Taxable brokerage, savings
  - Purpose: Bridge to Social Security

Bucket 2: Ages 59.5-65 (Early retirement, no Medicare)
  - Target withdrawal rate: 4.5%
  - Can use: All accounts (penalty-free 59.5)
  - Must account for: Healthcare costs (no Medicare)

Bucket 3: Ages 65-67 (Medicare available, no Social Security)
  - Target withdrawal rate: 3.5%
  - Can use: All accounts including HSA
  - Healthcare costs reduce (Medicare coverage)

Bucket 4: Ages 67+ (Social Security available)
  - Target withdrawal rate: 2.5% (lower due to SS income)
  - Can use: All accounts (flexibility with SS backup)
  - Healthcare covered (Medicare + SS income)
```

#### Calculator Features

##### Bucket Definition
- **Time Period**:
  - Start age or retirement year
  - End age or year (or "end of life")
  - Support overlap detection and warnings

- **Withdrawal Parameters**:
  - Target withdrawal rate (%)
  - Minimum withdrawal floor (absolute dollar amount)
  - Maximum withdrawal ceiling (absolute dollar amount)
  - Override: Allow manual withdrawal amount for special years

- **Account Constraints**:
  - Allowed account types (multi-select)
  - Prohibited account types
  - Withdrawal order/priority
  - RMD handling (mandatory vs optional)

- **Special Considerations**:
  - Tax-loss harvesting flag
  - Roth conversion opportunity flag
  - Healthcare cost adjustments
  - Social Security integration (expected annual income)
  - Pension income adjustments

##### Calculation Engine
- **Portfolio Projection**:
  - Start with complex portfolio (all accounts)
  - For each year in retirement:
    1. Identify which bucket applies (based on age)
    2. Calculate withdrawal amount (rate × portfolio value, adjusted for constraints)
    3. Select accounts to withdraw from (respecting constraints)
    4. Apply account-specific growth rates
    5. Record withdrawal details and remaining portfolio
    6. Move to next year

- **Outputs**:
  - Annual projection table:
    - Year/Age
    - Bucket (which period this falls in)
    - Target withdrawal rate
    - Withdrawal amount (calculated)
    - Withdrawal sources (which accounts)
    - Portfolio value before withdrawal
    - Growth/returns
    - Portfolio value after withdrawal
    - Notes (RMD applied, tax impact, etc.)

  - Summary Statistics:
    - Total withdrawals by period
    - Success rate (portfolio survives to life expectancy)
    - Failure scenarios (portfolio depleted, year of depletion)
    - Average withdrawal per period
    - Account balances at key milestones (65, 70, 80, 90)

##### Validation & Warnings
- **Overlap Detection**: Warn if bucket periods overlap
- **Gap Detection**: Warn if gaps exist between buckets
- **Rate Feasibility**: Flag if withdrawal rates are unsustainable
- **Constraint Conflicts**: Warn if constraints would prevent withdrawals
- **Early Access Penalties**: Flag withdrawals before age 59.5 from restricted accounts
- **RMD Violations**: Flag if RMD not being met

#### Database Schema Additions

```
WithdrawalBucket:
  - calculator (FK to CalculationScenario)
  - bucket_name (e.g., "Early Retirement")
  - start_age
  - end_age
  - start_year (optional, alternative to age)
  - end_year (optional)
  - target_withdrawal_rate (Float, %)
  - min_withdrawal_amount (Decimal, optional)
  - max_withdrawal_amount (Decimal, optional)
  - allowed_account_types (JSON: [list of account type codes])
  - prohibited_account_types (JSON: [list of account type codes])
  - withdrawal_order (JSON: [ordered list of account ids])
  - tax_loss_harvesting_enabled (Boolean)
  - roth_conversion_enabled (Boolean)
  - healthcare_cost_adjustment (Decimal, $)
  - expected_pension_income (Decimal, $/year)
  - expected_social_security_income (Decimal, $/year)
  - notes (text field)
  - order (Integer, for sorting)
  - created_date
  - updated_date

BucketedWithdrawalResult:
  - calculation (FK to CalculationResult)
  - year (Integer)
  - age (Integer)
  - bucket (FK to WithdrawalBucket)
  - target_rate (Float)
  - calculated_withdrawal (Decimal)
  - actual_withdrawal (Decimal)
  - withdrawal_accounts (JSON: {account_id: amount})
  - portfolio_value_start (Decimal)
  - investment_growth (Decimal)
  - portfolio_value_end (Decimal)
  - notes (text field)
```

#### API Endpoints

##### Bucket Management
- `POST /api/v1/scenarios/{id}/buckets/` - Create withdrawal bucket
- `GET /api/v1/scenarios/{id}/buckets/` - List all buckets for scenario
- `GET /api/v1/scenarios/{id}/buckets/{bucket_id}/` - Get bucket details
- `PUT /api/v1/scenarios/{id}/buckets/{bucket_id}/` - Update bucket
- `DELETE /api/v1/scenarios/{id}/buckets/{bucket_id}/` - Delete bucket
- `POST /api/v1/scenarios/{id}/buckets/validate/` - Validate all buckets (check overlaps, gaps)

##### Calculation
- `POST /api/v1/calculations/bucketed-withdrawal/` - Run bucketed withdrawal calculation
- `GET /api/v1/calculations/{id}/results/bucketed/` - Get detailed results
- `GET /api/v1/calculations/{id}/summary/bucketed/` - Get summary statistics

#### Frontend - Bucketed Withdrawal UI

##### Pages to Build
- **Bucket Builder** (Visual bucket creation)
  - Timeline view showing age ranges and withdrawal rates
  - Drag-to-resize buckets, click to edit
  - Bucket overlap warning visualization
  - Add/remove bucket buttons

- **Bucket Editor** (Detailed configuration form)
  - Age range inputs (start/end)
  - Withdrawal rate input
  - Min/max withdrawal fields
  - Account type multi-select (allowed/prohibited)
  - Priority reordering (drag-drop account order)
  - Special considerations section

- **Calculation Results** (Visualization and analysis)
  - Timeline chart: withdrawal rate and portfolio value over time
  - Table: annual projections with all details
  - Account breakdown: which accounts were used each year
  - Success metrics: sustainability analysis
  - Export: PDF and CSV options

- **Scenario Comparison** (Compare multiple bucket strategies)
  - Side-by-side bucket configurations
  - Outcome comparison (which lasts longer, safer, etc.)
  - Recommendation engine (which strategy best fits goals)

#### Calculation Examples

##### Example 1: Three-Bucket Strategy
```
Input: Portfolio of $1,000,000
  - $300K taxable brokerage
  - $400K Traditional IRA
  - $300K Roth IRA

Bucket 1: Age 55-59.5 (5 years)
  - Rate: 2%
  - Accounts: Taxable only
  - Withdrawal: $20,000/year from taxable ($100K over 5 years)

Bucket 2: Age 59.5-67 (7.5 years)
  - Rate: 4%
  - Accounts: All
  - Withdrawal: ~$40,000/year (accounts deplete at different rates)

Bucket 3: Age 67+ (life expectancy)
  - Rate: 3% (with $20K Social Security)
  - Accounts: All (Roth preferred for tax efficiency)
  - Withdrawal: $30,000/year total needed

Output: Portfolio survives to age 98 with success rate 85% (historical)
```

##### Example 2: Five-Bucket Strategy (From Requirements)
```
Bucket 1: Ages 55-59.5 (Pre-retirement, no 401k access)
  - Rate: 1.5% (very conservative)
  - Accounts: Savings, taxable brokerage only
  - Purpose: Live off savings until 401k accessible

Bucket 2: Ages 59.5-65 (Early retirement, expensive healthcare)
  - Rate: 4%
  - Accounts: All (401k/IRA penalty-free at 59.5)
  - Special: +$5,000/year healthcare cost adjustment

Bucket 3: Ages 65-67 (Medicare available, no SS)
  - Rate: 3.5%
  - Accounts: All + HSA
  - Special: -$3,000/year healthcare cost (Medicare reduces costs)

Bucket 4: Ages 67-75 (Social Security available)
  - Rate: 2%
  - Accounts: All (flexibility with SS backup)
  - Special: +$30,000/year Social Security income (built in)

Bucket 5: Ages 75+ (Later years, lower needs)
  - Rate: 1.5%
  - Accounts: All (all restrictions passed)
  - Purpose: Ultra-conservative (long life expectancy)
```

### 2.1.3 Calculator Enhancements for 4% and 4.7%

These calculators will be updated to support:
- Complex multi-account portfolios (from 2.0)
- Account-specific withdrawal restrictions
- Tax-aware withdrawal sequencing
- Account type preferences (which to withdraw from first)
- RMD integration
- Simpler output than Bucketed calculator (single rate throughout)

### 2.1.4 Testing Requirements

- **Unit Tests**:
  - Bucket validation (no overlaps, no gaps)
  - Withdrawal rate calculations
  - Account constraint enforcement
  - Growth rate application
  - RMD calculations

- **Integration Tests**:
  - Full end-to-end calculation with complex portfolio
  - Multiple bucket scenarios
  - Account depletion scenarios
  - Tax impact calculations
  - Account switching (switch withdrawals between accounts)

- **Edge Cases**:
  - Very long retirement (100+ years)
  - Negative growth years (market crash)
  - Account depleted mid-year
  - Single account portfolio
  - All constraints violated (no valid accounts)
  - Zero withdrawal year

### 2.1.5 Deliverables for 2.1

- Reworked 4% and 4.7% rule calculators with portfolio support
- Dynamic Bucketed Withdrawal Rate calculator
- Database models for buckets and results
- Comprehensive API endpoints
- Frontend UI for bucket creation and management
- Calculation results visualization
- Extensive test coverage
- Documentation and examples

---

## 2.2 Asynchronous Calculation Processing

**Goal**: Enable long-running calculations to execute asynchronously with progress tracking.

### 2.2.1 Celery Task Queue Integration
- Celery task queue integration
- Redis broker configuration
- Task status tracking (pending, running, completed, failed)
- Progress percentage updates (via WebSocket or polling)
- Retry logic for failed calculations
- Result caching for repeated scenarios

### 2.2.2 Implementation Details
- Wrap advanced calculators (Monte Carlo, historical analysis) in Celery tasks
- Implement progress callback mechanism
- Store results in database with expiration policy
- WebSocket support for real-time progress updates
- Fallback to polling for browsers without WebSocket

### 2.2.3 API Endpoints
- `POST /api/v1/calculations/async/` - Start async calculation
- `GET /api/v1/calculations/{id}/status/` - Get calculation status
- `GET /api/v1/calculations/{id}/progress/` - Get detailed progress
- `GET /api/v1/calculations/{id}/results/` - Get completed results
- `DELETE /api/v1/calculations/{id}/` - Cancel calculation

---

## 2.3 Advanced Calculation Engines (Original)

### 2.3.1 Monte Carlo Simulator
- **Configurable iterations** (1k to 100k)
- **Asset class volatility modeling**
- **Inflation adjustment**
- **Sequence-of-returns risk analysis**
- **Probability of success output**

### 2.3.2 Historical Period Analysis
- **Test against actual market returns** (1960s-present)
- **Best/worst case scenarios**
- **Identify vulnerable periods**

### 2.3.3 Sensitivity Analysis
- **What-if modeling**: adjust returns, spending, inflation
- **Impact visualization**

### 2.3.4 Tax-Aware Calculations
- **Basic income tax estimation**
- **Account withdrawal sequencing** (Roth vs Traditional)

---

## 2.4 Advanced Visualization

- Confidence bands (Monte Carlo probability ranges)
- Scenario comparison charts (side-by-side projections)
- Heatmaps (sensitivity analysis results)
- Distribution charts (Monte Carlo outcomes)
- Interactive drill-down (annual detail views)
- Export to PDF with charts

---

## 2.5 Scenario Comparison

- Compare multiple scenarios side-by-side
- Metrics dashboard: success rate, avg portfolio size, withdrawal flexibility
- Graphical comparison of outcomes

---

## 2.6 Frontend Enhancements

- Monte Carlo visualization with progress indicator (Chart.js + HTMX polling)
- Scenario comparison page (Django template + advanced charts)
- Historical analysis drill-down (HTMX partial updates)
- What-if scenario builder (Alpinejs for interactive parameter adjustment)
- Advanced settings page for calculation parameters
- Export functionality (PDF via reportlab, CSV)

---

## 2.7 Database Enhancements

- Calculation results caching
- Historical market data table (optional external API integration)
- Audit log for scenario changes

---

## Phase 2 Deliverables (Updated)

**Foundational**:
- Advanced multi-account portfolio system (2.0)
  - 10+ account types supported
  - Automatic value history tracking
  - Full portfolio dashboard

**Calculation Engines**:
- Reworked 4% and 4.7% rule calculators with portfolio support (2.1)
- Dynamic Bucketed Withdrawal Rate calculator (NEW in 2.1)
- Monte Carlo calculation engine (100k simulations) (2.3)
- Historical period backtesting (2.3)
- Sensitivity analysis (2.3)

**Processing & Analysis**:
- Async task processing with Celery (2.2)
- Advanced charting and visualization (2.4)
- Scenario comparison tools (2.5)

**Export & UI**:
- PDF export with charts (2.6)
- Tax-aware calculations (MVP level) (2.3)
- Enhanced frontend for bucket builder, portfolio management, scenario comparison (2.6)

---

## Implementation Priority

1. **2.0 Advanced Portfolio** - Foundation for all other features
2. **2.1 Enhanced Calculators** - Core calculation engines (rework 4%/4.7%, add bucketed)
3. **2.2 Async Processing** - Required for long-running calculations
4. **2.3 Advanced Engines** - Monte Carlo, historical, sensitivity
5. **2.4-2.7** - Visualization, comparison, database, frontend polish

**Note**: 2.0 and 2.1 must be completed before other sections can be properly tested.
