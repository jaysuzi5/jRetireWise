# jRetireWise - Retirement Calculator Platform Plan

## Project Overview

jRetireWise is a professional retirement planning application that enables users to track financial information, model retirement scenarios, and make data-driven retirement decisions. The application will support advanced retirement calculation methodologies including deterministic rules (4% rule, 4.7% rule) and sophisticated stochastic simulations (Monte Carlo, sensitivity analysis, historical period analysis).

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: Django 5.0+ with Django REST Framework (DRF)
- **Database**: PostgreSQL 14+
- **Task Queue**: Celery with Redis broker (for async financial calculations)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Observability**: OpenTelemetry (Python SDK) with collector integration

### Frontend
- **Language**: Python (Django templates) + JavaScript/HTML5
- **Templating**: Django templates with Jinja2
- **Charting**: Chart.js (vanilla JavaScript)
- **Styling**: Tailwind CSS (for professional appearance)
- **Interactivity**: HTMX for dynamic interactions (form submissions, dynamic content loading)
- **Form Handling**: Django forms with client-side validation (Alpinejs for light interactivity)

### Deployment & Infrastructure
- **Container Runtime**: Docker
- **Orchestration**: Kubernetes (home cluster)
- **Reverse Proxy**: Nginx or Traefik
- **Static Files**: Served via Nginx or Django whitenoise
- **Secrets Management**: Kubernetes secrets
- **Configuration**: Environment variables via ConfigMaps

### Authentication
- **OAuth2 Provider**: Google OAuth 2.0
- **Authorization**: Token-based (JWT)
- **Session Management**: HTTP-only cookies with CSRF protection

## Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│              Django Application (Unified)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ View Layer (Class/Function Views)                    │   │
│  │ - HTML rendering via Django templates               │   │
│  │ - Google OAuth authentication                        │   │
│  │ - Form processing and validation                     │   │
│  │ - Session management                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Layer (Django REST Framework)                    │   │
│  │ - RESTful endpoints for AJAX/HTMX requests          │   │
│  │ - JSON responses for dynamic content                │   │
│  │ - Calculation status polling                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Business Logic Layer                                 │   │
│  │ - Financial calculation engines                      │   │
│  │ - Scenario builders                                  │   │
│  │ - Results processors                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Database Models & Serializers                        │   │
│  │ - User, Financial Data, Scenarios, Results          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Frontend Assets                                       │   │
│  │ - HTML templates (Django templates)                  │   │
│  │ - JavaScript (Chart.js, HTMX, Alpinejs)            │   │
│  │ - CSS (Tailwind)                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
         │               │               │
         │               │               │
    ┌────▼────┐   ┌──────▼──────┐  ┌───▼──────┐
    │PostgreSQL│   │  Redis/     │  │OpenTelem│
    │Database  │   │  Celery     │  │Collector│
    └──────────┘   │  (Async     │  └─────────┘
                   │  Tasks)     │
                   └─────────────┘
```

### Key Components

#### 1. **Authentication & User Management**
- Google OAuth 2.0 integration via `django-allauth`
- Django session-based authentication for template views
- API token authentication for AJAX/HTMX requests (Token or Session-based)
- User profile model storing financial information, preferences
- Role-based access (initially single-user focus, extensible for future multi-tenant)

#### 2. **Financial Data Management**
- User asset models: cash, stocks, bonds, real estate, retirement accounts
- Income sources: salary, Social Security estimates, pension, rental income
- Expenses: fixed, variable, one-time, healthcare
- Investment allocation and performance tracking
- Historical return data integration

#### 3. **Calculation Engines**
- **Deterministic Calculators**: 4% rule, 4.7% rule, fixed percentage withdrawals
- **Stochastic Engine**: Monte Carlo simulator with configurable iterations (1k-100k+)
- **Historical Analysis**: Backtesting against historical market periods (S&P 500, bonds)
- **Sensitivity Analysis**: What-if scenario modeling
- **Tax Calculations**: Basic income tax considerations
- All calculations return detailed breakdown data for visualization

#### 4. **Scenario Management**
- Create, store, and compare multiple retirement scenarios
- Version control for scenario modifications
- Parameter templates (pessimistic, realistic, optimistic)
- Scenario comparison visualization

#### 5. **Reporting & Visualization**
- Portfolio balance projection over time
- Success rate probability (Monte Carlo)
- Annual withdrawal amount tracking
- Tax projection estimates
- Market condition sensitivity heatmaps
- Interactive dashboard with customizable widgets
- Export capabilities (PDF, CSV)

#### 6. **Observability**
- OpenTelemetry instrumentation:
  - HTTP request spans (latency, status)
  - Database query spans
  - Celery task execution spans
  - Custom financial calculation metrics
- Structured logging with context (user ID, scenario ID, calculation ID)
- Metrics: API response times, calculation durations, success rates

## Data Model (Core Entities)

```
User
├── id (UUID)
├── email
├── google_oauth_id
├── full_name
├── created_at
├── updated_at
└── preferences (JSON: theme, notification settings)

FinancialProfile
├── user_id (FK)
├── current_age
├── retirement_age
├── life_expectancy
├── annual_spending
├── social_security_annual
├── pension_annual
└── updated_at

Asset
├── user_id (FK)
├── name
├── type (cash, stock, bond, real_estate, retirement_account)
├── current_value
├── annual_return_rate (average)
├── created_at
└── updated_at

RetirementScenario
├── user_id (FK)
├── name
├── description
├── calculation_type (4percent, 4.7percent, montecarlo, historical)
├── parameters (JSON: customizable inputs)
├── created_at
├── updated_at
└── is_default

CalculationResult
├── scenario_id (FK)
├── calculation_type
├── status (pending, completed, failed)
├── result_data (JSON: annual projections, success rates, etc.)
├── execution_time_ms
├── created_at
└── updated_at

CalculationTask (for async jobs)
├── id (UUID)
├── scenario_id (FK)
├── celery_task_id
├── status
├── progress_percentage
├── created_at
└── updated_at
```

## Implementation Phases

### Phase 1: MVP (Minimum Viable Product) - 8-12 weeks

**Goal**: Establish core platform with foundational retirement calculations and Google OAuth authentication.

#### 1.1 Project Setup & Infrastructure
- Django project structure with proper settings management (dev, prod)
- PostgreSQL database initialization
- Docker containerization
- Kubernetes manifests (single deployment, service, configmap, secrets)
- GitHub Actions CI/CD pipeline (tests, linting, build, deploy)
- OpenTelemetry integration and local collector setup
- DRF configuration with CORS for frontend domain
- API documentation setup (drf-spectacular)

#### 1.2 Authentication & User Management
- Google OAuth 2.0 integration
- JWT token authentication for API
- User profile model and endpoints
- Login/logout endpoints
- User preferences (basic)

#### 1.3 Financial Data Management
- Asset management (CRUD endpoints)
- Financial profile endpoints (age, retirement goals, spending)
- Income source tracking
- Basic expense tracking
- Data validation and serializers

#### 1.4 Calculation Engines (MVP)
- **4% Rule Calculator**: Simple annual withdrawal calculation
- **4.7% Rule Calculator**: Enhanced safe withdrawal rate
- **Fixed Percentage Withdrawal**: User-defined percentage
- Results stored in database
- Synchronous calculation (no async yet)
- Output: annual breakdown, success metrics

#### 1.5 Scenario Management
- Create and store named scenarios
- Parameter template system (pessimistic, realistic, optimistic)
- List/retrieve/update/delete scenarios
- Clone scenario functionality

#### 1.6 Frontend - Django Templates with AJAX/HTMX
- **Layout**: Header (logo, user menu), sidebar navigation, main content area (server-rendered)
- **Pages** (Django template views):
  - Dashboard: Quick stats, primary scenario summary
  - Profile: User info, financial data entry
  - Scenarios: List, create, edit scenarios
  - Analysis: Single scenario results with charts
  - Settings: User preferences, logout
- **Frontend Technologies**:
  - Django templates for HTML structure and dynamic rendering
  - HTMX for dynamic interactions (form submissions, partial page updates)
  - Chart.js (vanilla JavaScript) for professional chart rendering
  - Alpinejs for lightweight client-side interactivity
  - Tailwind CSS for professional, responsive styling
- **API Integration**:
  - DRF endpoints for AJAX requests
  - HTMX for dynamic content loading without page refresh
  - JSON responses for chart data and status updates

#### 1.7 Deployment & DevOps
- Docker build and push to registry
- Kubernetes manifests (deployment, service, ingress)
- Persistent volume for database
- Environment configuration via ConfigMaps/Secrets
- Health checks and liveness probes
- Nginx reverse proxy configuration

#### 1.8 Testing & Documentation
- Unit tests for calculation engines (pytest)
- API endpoint tests (pytest with DRF test utilities)
- Template view tests (Django test framework)
- API documentation (Swagger/OpenAPI via drf-spectacular)
- CLAUDE.md updated with build, test, and deploy commands
- Architecture documentation

**MVP Deliverables**:
- Working Django application with Google OAuth
- Django templates with professional UI (Tailwind CSS)
- Two simple calculators (4%, 4.7%)
- Scenario management with HTMX interactions
- Single Kubernetes deployment
- OpenTelemetry integration
- Complete test coverage for calculation logic
- API and template documentation

---

### Phase 2: Enhanced Analytics & Sophisticated Calculations - 6-8 weeks

**Goal**: Add Monte Carlo simulations, historical analysis, and advanced visualization.

#### 2.1 Advanced Calculation Engines
- **Monte Carlo Simulator**:
  - Configurable iterations (1k to 100k)
  - Asset class volatility modeling
  - Inflation adjustment
  - Sequence-of-returns risk analysis
  - Probability of success output
- **Historical Period Analysis**:
  - Test against actual market returns (1960s-present)
  - Best/worst case scenarios
  - Identify vulnerable periods
- **Sensitivity Analysis**:
  - What-if modeling: adjust returns, spending, inflation
  - Impact visualization
- **Tax-Aware Calculations**:
  - Basic income tax estimation
  - Account withdrawal sequencing (Roth vs Traditional)

#### 2.2 Asynchronous Calculation Processing
- Celery task queue integration
- Redis broker
- Task status tracking (pending, running, completed, failed)
- Progress percentage updates (via WebSocket or polling)
- Retry logic for failed calculations
- Result caching for repeated scenarios

#### 2.3 Advanced Visualization
- Confidence bands (Monte Carlo probability ranges)
- Scenario comparison charts (side-by-side projections)
- Heatmaps (sensitivity analysis results)
- Distribution charts (Monte Carlo outcomes)
- Interactive drill-down (annual detail views)
- Export to PDF with charts

#### 2.4 Scenario Comparison
- Compare multiple scenarios side-by-side
- Metrics dashboard: success rate, avg portfolio size, withdrawal flexibility
- Graphical comparison of outcomes

#### 2.5 Frontend Enhancements
- Monte Carlo visualization with progress indicator (Chart.js + HTMX polling)
- Scenario comparison page (Django template + advanced charts)
- Historical analysis drill-down (HTMX partial updates)
- What-if scenario builder (Alpinejs for interactive parameter adjustment)
- Advanced settings page for calculation parameters
- Export functionality (PDF via reportlab, CSV)

#### 2.6 Database Enhancements
- Calculation results caching
- Historical market data table (optional external API integration)
- Audit log for scenario changes

**Phase 2 Deliverables**:
- Monte Carlo calculation engine (100k simulations)
- Historical period backtesting
- Sensitivity analysis
- Async task processing with Celery
- Advanced charting and visualization
- Scenario comparison tools
- PDF export
- Tax-aware calculations (MVP level)

---

### Phase 3: Professional Features & Enhancements - 4-6 weeks

**Goal**: Polish and add professional-grade features.

#### 3.1 Advanced Features
- **Account Aggregation**: Direct bank/brokerage data import (via Plaid API, optional)
- **Life Expectancy Modeling**: Health factor questionnaire
- **Estate Planning**: Beneficiary tracking, inheritance scenarios
- **Inflation Scenarios**: Fixed vs historical inflation modeling
- **Social Security Optimization**: Claiming age analysis
- **Healthcare Cost Projection**: Age-based healthcare expense modeling

#### 3.2 Reporting & Analytics
- Comprehensive PDF retirement plan report
- Annual plan review recommendations
- Goal tracking and milestones
- Downloadable detailed analysis (Excel with multiple sheets)
- Summary statistics and key metrics
- Trend analysis (portfolio progress tracking)

#### 3.3 Performance Optimization
- Database query optimization and indexing
- Calculation result caching strategies
- Frontend bundle optimization
- Image optimization and lazy loading
- API response caching (Redis)

#### 3.4 Additional Observability
- Performance dashboards (via OpenTelemetry)
- Alert thresholds for long-running calculations
- User activity analytics
- Error tracking and alerting
- Custom business metrics (calculation success rates by type)

#### 3.5 UI/UX Refinements
- Onboarding wizard for new users (Django forms + templates)
- Guided scenario creation (step-by-step with HTMX)
- Improved asset management interface (Alpinejs for interactivity)
- Dark mode support (CSS variants via Tailwind)
- Mobile responsive improvements (prep for future mobile)
- Accessibility improvements (WCAG 2.1 AA)

#### 3.6 Documentation & Support
- User guide with screenshots
- Video tutorials for common tasks
- Glossary of retirement planning terms
- FAQ section
- In-app help tooltips

**Phase 3 Deliverables**:
- Advanced financial features (Social Security, healthcare, inflation)
- Professional reporting system
- Performance optimizations
- Enhanced observability and analytics
- Polished UI/UX
- Complete user documentation

---

## Non-Functional Requirements

### Security
- HTTPS/TLS for all communications
- CSRF protection on all state-changing endpoints
- SQL injection prevention (Django ORM)
- XSS protection (React escaping, Django templates)
- Password security (if ever needed for backup auth)
- Secure headers (CSP, X-Frame-Options, etc.)
- Rate limiting on authentication endpoints
- Data encryption at rest (PostgreSQL encryption)
- Google OAuth scope: email, profile only

### Scalability
- Database connection pooling (pgBouncer or Django connection pooling)
- Stateless API design for horizontal scaling
- Redis for caching and task queue
- Database indexes on frequently queried fields
- Pagination for list endpoints
- Async processing for heavy calculations

### Reliability
- Database backups (daily via Kubernetes CronJob)
- Health check endpoints
- Graceful error handling and user feedback
- Calculation timeout handling
- Transaction management for data consistency
- Retry logic for async tasks (Celery)

### Maintainability
- Clean code standards (PEP 8 for Python, ESLint for JavaScript)
- Comprehensive test coverage (aim for 80%+)
- Modular architecture
- Clear separation of concerns
- Detailed code comments for complex logic
- API versioning strategy (v1, v2, etc.)
- Database migration strategy (Alembic or Django migrations)

### Performance
- API response time target: <200ms for most endpoints
- Calculation execution: <5 seconds for simple calculators, <30 seconds for Monte Carlo (100k iterations)
- Frontend page load: <2 seconds
- Database query optimization (explain plans, indexes)
- Async processing for long-running tasks

### Observability
- OpenTelemetry instrumentation for all services
- Structured logging with context (user ID, request ID, calculation ID)
- Metrics: latency, throughput, error rates
- Distributed tracing support
- Local collector for development, configurable for production

## Testing Strategy

jRetireWise employs a comprehensive testing strategy following the testing pyramid: many unit tests, fewer integration tests, and select UI/end-to-end tests. All phases must pass all test suites before code is merged and deployed.

### Testing Pyramid

```
        /\
       /  \  UI/E2E Tests (Smoke Tests)
      /____\  ~10% of tests
     /      \
    /  ___   \  Integration Tests
   /  /     \ \ ~20% of tests
  /  /       \ \
 /  /__   ____\ \
/__________\____\ Unit Tests
   ~70% of tests
```

### 1. Unit Tests

**Scope**: Individual functions, classes, and modules in isolation

**Technologies**:
- **Framework**: pytest (Python testing framework)
- **Mocking**: pytest-mock, unittest.mock
- **Coverage**: pytest-cov
- **Target Coverage**: ≥80% for all modules

**What to Test**:
- Financial calculation engines (4%, 4.7%, Monte Carlo, historical analysis)
- Data validation and serializers
- Business logic (scenario builders, calculation processors)
- Utility functions
- Model methods and properties

**Execution**:
```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage report
pytest tests/unit/ --cov=jretirewise --cov-report=html

# Run specific test file
pytest tests/unit/calculations/test_four_percent_calculator.py

# Run tests matching pattern
pytest tests/unit/ -k "calculator"
```

**Requirements**:
- All unit tests must pass before committing code
- Coverage must not decrease
- Test file structure mirrors source structure: `tests/unit/<module>/<entity>/test_<file>.py`

### 2. Integration Tests

**Scope**: API endpoints, database interactions, task queues, and cross-module functionality

**Technologies**:
- **Framework**: pytest with Django test utilities
- **Database**: PostgreSQL test database (auto-created per test session)
- **Fixtures**: pytest-django fixtures for database, client, user setup
- **Task Queue**: Celery test worker (in-process execution)
- **Factory Pattern**: factory-boy for test data creation

**What to Test**:
- **API Endpoints**: DRF view tests with full request/response cycle
  - Authentication flows (Google OAuth, token auth, session auth)
  - CRUD operations for users, assets, scenarios, calculations
  - Permission and authorization checks
  - Input validation and error responses
- **Database Transactions**: Data persistence, relationships, constraints
- **Async Tasks**: Celery task execution, retries, failure handling
- **Business Workflows**: End-to-end scenarios (create user → add assets → run calculation)
- **Template Rendering**: View responses return correct templates and context

**Execution**:
```bash
# Run all integration tests
pytest tests/integration/

# Run integration tests for API
pytest tests/integration/api/

# Run with database and fixtures
pytest tests/integration/ -v --tb=short

# Run specific test class
pytest tests/integration/api/test_scenarios.py::TestScenarioCRUD
```

**Database Setup**:
- Use pytest-django's `db` fixture for tests requiring database
- Transaction-based isolation (rollback after each test)
- Fixtures auto-cleaned up
- Test data created via factory-boy factories

**Example Structure**:
```
tests/integration/
├── api/
│   ├── test_authentication.py
│   ├── test_scenarios.py
│   ├── test_calculations.py
│   └── test_assets.py
├── models/
│   ├── test_user.py
│   ├── test_scenario.py
│   └── test_calculation_result.py
└── tasks/
    └── test_async_calculations.py
```

### 3. UI/End-to-End Tests (Smoke Tests)

**Scope**: User workflows from login through calculation and result viewing

**Technologies**:
- **Framework**: Playwright (browser automation)
- **Language**: Python with pytest-playwright
- **Browsers**: Chromium (primary), Firefox (optional for cross-browser)
- **Execution**: Headless by default, headed mode for debugging
- **Reporting**: Screenshot/video capture on failure, HTML reports

**What to Test** (Post-Deployment Smoke Tests):
- **Authentication Flow**:
  - Google OAuth login
  - Session persistence
  - Logout
  - Access denied for unauthenticated users
- **Happy Path Workflows**:
  - Create new scenario
  - Add financial data (assets, income, expenses)
  - Run 4% calculator and view results
  - Run Monte Carlo and verify progress indicator (Phase 2)
  - Compare scenarios (Phase 2)
  - Update scenario and recalculate
- **UI Rendering**:
  - Dashboard loads and displays data
  - Charts render without errors
  - Forms validate and submit correctly
  - Navigation works between pages
  - Responsive design (basic checks)
- **Error Handling**:
  - Invalid input shows error messages
  - Network errors handled gracefully (Phase 2)
  - Long-running calculations show progress (Phase 2)

**Execution**:
```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run smoke tests only (subset of E2E)
pytest tests/e2e/smoke/ -v

# Run in headed mode for debugging
pytest tests/e2e/smoke/test_calculator_workflow.py --headed

# Generate HTML report
pytest tests/e2e/ --html=report.html --self-contained-html
```

**Example Test Structure**:
```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_user_can_create_scenario_and_calculate():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to app
        await page.goto("http://localhost:8000")

        # Login with test user
        await page.click("text=Login")
        await page.fill("input[name=email]", "test@example.com")
        await page.fill("input[name=password]", "testpass123")
        await page.click("text=Sign In")

        # Create scenario
        await page.click("text=New Scenario")
        await page.fill("input[name=name]", "My Retirement Plan")
        await page.click("text=Create")

        # Add assets
        await page.click("text=Add Asset")
        # ... fill in asset details

        # Run calculation
        await page.click("text=Calculate")
        await page.wait_for_selector("canvas")  # Wait for chart

        # Verify results displayed
        assert await page.is_visible("text=Success Rate")
```

**Test File Organization**:
```
tests/e2e/
├── conftest.py  # Shared fixtures (browser, test server, test user)
├── smoke/
│   ├── test_authentication.py
│   ├── test_calculator_workflow.py
│   ├── test_scenario_management.py
│   └── test_ui_rendering.py
└── integration/  # More detailed workflow tests (Phase 2+)
    ├── test_monte_carlo_workflow.py
    └── test_scenario_comparison.py
```

**Post-Deployment Smoke Tests**:
Run against deployed application after each deployment:
```bash
# Test against staging/production
pytest tests/e2e/smoke/ --base-url="https://jretirewise.home.k8s"

# Rollback if smoke tests fail
# (Automated via CI/CD pipeline)
```

### 4. Test Data & Fixtures

**Test Fixtures** (via pytest and factory-boy):
- `db_user`: Test user with Google OAuth profile
- `db_financial_profile`: User with complete financial data
- `db_scenario`: Pre-created scenario with parameters
- `db_calculation_result`: Completed calculation for validation
- `api_client`: Authenticated API client
- `test_browser`: Playwright browser instance (E2E)

**Factory Definitions**:
```python
# tests/factories.py
import factory
from django.contrib.auth import get_user_model
from jretirewise.financial.models import Asset, Scenario

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    google_oauth_id = factory.Sequence(lambda n: f"google_id_{n}")
    full_name = "Test User"

class AssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Asset

    user = factory.SubFactory(UserFactory)
    name = "Portfolio"
    type = "stock"
    current_value = 500000
    annual_return_rate = 0.07
```

### 5. Test Coverage Requirements

**By Phase**:

| Component | MVP | Phase 2 | Phase 3 |
|-----------|-----|---------|---------|
| Unit Tests | ≥80% | ≥85% | ≥85% |
| Calculation Engines | 100% | 100% | 100% |
| API Views | ≥75% | ≥80% | ≥85% |
| Models | ≥85% | ≥85% | ≥90% |
| Integration Tests | 10+ | 20+ | 30+ |
| E2E/Smoke Tests | 5+ | 10+ | 15+ |

### 6. CI/CD Integration

**GitHub Actions Workflow**:

```yaml
name: Tests & Quality

on: [push, pull_request]

jobs:
  tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11

      # Unit Tests
      - name: Run Unit Tests
        run: |
          pip install -r requirements.txt
          pytest tests/unit/ --cov=jretirewise

      # Integration Tests
      - name: Run Integration Tests
        run: pytest tests/integration/ -v

      # Code Quality
      - name: Lint with flake8
        run: flake8 jretirewise tests

      # Upload coverage
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  # UI Tests run separately (slower)
  ui-tests:
    runs-on: ubuntu-latest
    needs: tests

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium

      - name: Run E2E Tests
        run: pytest tests/e2e/smoke/ -v

  # Post-deployment smoke tests
  smoke-tests:
    runs-on: ubuntu-latest
    needs: deploy
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium

      - name: Run Smoke Tests Against Deployed App
        run: |
          pytest tests/e2e/smoke/ \
            --base-url="https://jretirewise.home.k8s" \
            -v

      - name: Rollback on Failure
        if: failure()
        run: |
          # Trigger rollback deployment
          kubectl rollout undo deployment/jretirewise -n jretirewise
          exit 1
```

### 7. Local Testing Workflow

**Developer Pre-Commit Checks**:
```bash
# Run all tests locally before push
pytest tests/unit/ --cov=jretirewise --cov-fail-under=80
pytest tests/integration/
pytest tests/e2e/smoke/

# Or use provided script
./scripts/run_all_tests.sh
```

**Git Pre-Commit Hook**:
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest tests/unit/ -q || exit 1
flake8 jretirewise --count || exit 1
```

### 8. Test Maintenance & Best Practices

**Test Naming Convention**:
- Unit: `test_<function>_<scenario>`
  - Example: `test_four_percent_calculator_success_rate_calculation`
- Integration: `Test<Entity><Action>` class-based
  - Example: `TestScenarioCreation`, `TestAssetUpdate`
- E2E: `test_user_can_<workflow>`
  - Example: `test_user_can_create_and_run_scenario`

**Test Documentation**:
- Each test file has docstring explaining purpose
- Complex test logic has inline comments
- Fixtures documented with purpose

**Test Stability**:
- Use fixed test data (not current date/time)
- Mock external dependencies (Google OAuth, market data APIs)
- Retry logic for flaky network-dependent tests (Phase 2+)
- Use appropriate waits in E2E tests (not fixed sleeps)

**Continuous Improvement**:
- Review failing tests in CI
- Update tests when requirements change
- Keep test dependencies up-to-date
- Monitor test execution time (optimize slow tests)

## Deployment & DevOps

### Container Strategy
- Single Dockerfile for unified Django application (Python + static files)
- Docker Compose for local development
- Base image: python:3.11-slim
- Static files (CSS, JavaScript, images) collected via Django staticfiles

### Kubernetes Manifests
- Single namespace for application
- Deployment: Django backend (1+ replicas for HA)
- StatefulSet: PostgreSQL (single instance, persistent volume)
- Service: Expose backend API and frontend
- Ingress: Route traffic, TLS termination
- ConfigMap: Environment-specific configuration
- Secret: Database credentials, Google OAuth secrets, JWT keys
- PersistentVolumeClaim: Database storage
- ServiceMonitor: Prometheus scraping (if available)

### Upgrade Strategy
- Blue-green deployment (old version runs alongside new)
- Database migration runs before deployment cutover
- Automatic rollback on health check failure
- Zero-downtime deployments

### Monitoring & Logging
- OpenTelemetry collector sidecar or standalone
- Prometheus for metrics (optional)
- ELK/Loki for log aggregation (optional)
- Application logs to stdout (container best practice)

## Development Workflow

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
celery -A config worker -l info

# Collect static files (CSS, JS, images)
python manage.py collectstatic

# Testing
pytest
```

### Version Control
- Main branch: production-ready code
- Feature branches: `feature/description`
- Pull requests for code review
- Commit messages: conventional commits format

### CI/CD Pipeline (GitHub Actions)

**Pipeline Stages**:

1. **On Pull Request (PR)**:
   - Run unit tests (pytest)
   - Run integration tests
   - Run linting and code quality checks (flake8, black)
   - Run E2E smoke tests against test build
   - Block merge if any tests fail

2. **On Main Branch Merge**:
   - All PR checks pass
   - Build Docker image with semantic versioning tag
   - Push image to Docker Hub
   - Update Kubernetes manifests with new image tag
   - Trigger ArgoCD deployment workflow
   - Run post-deployment smoke tests
   - Automatic rollback on smoke test failure

**Docker Hub Publishing**:
- Image naming: `dockerhubuser/jretirewise:v1.2.3` (semantic versioning)
- Also tag as `latest` for convenience
- Credentials stored in GitHub Secrets
- Images include build metadata (commit SHA, build date)

**Dockerfile Considerations**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py shell -c "from django.core.management import call_command; call_command('migrate', verbosity=0)" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

**ArgoCD Integration**:
- Separate Git repository for Kubernetes manifests (`jretirewise-argocd`)
- GitHub Actions updates manifest repo on successful Docker build
- ArgoCD monitors manifest repo and auto-syncs to cluster
- Manual sync option for rollbacks or urgent changes
- Notifications on deployment success/failure

**GitHub Actions Workflow Overview**:

```
PR Opened/Updated
    ↓
Unit Tests → Integration Tests → Linting → E2E Tests
    ↓ (all pass)
Merge to Main
    ↓
Build Docker Image → Push to Docker Hub
    ↓
Update Manifests Repo → Commit and Push
    ↓
ArgoCD Detects Change → Syncs to Kubernetes
    ↓
Post-Deployment Smoke Tests
    ↓ (fail)
Automatic Rollback (kubectl rollout undo)
```

**Environment Variables & Secrets Management**:
- GitHub Secrets for sensitive values:
  - `DOCKER_HUB_USERNAME` and `DOCKER_HUB_TOKEN`
  - `ARGOCD_SERVER` and `ARGOCD_AUTH_TOKEN`
  - `KUBECONFIG` (if needed for direct kubectl access)
- Kubernetes Secrets for runtime config:
  - Database credentials
  - Google OAuth client ID/secret
  - OpenTelemetry collector endpoint
- ConfigMaps for non-sensitive config:
  - Database host/port
  - Redis host/port
  - Application log level

### Database Management

**PostgreSQL Backup Strategy**:
- Automated daily backups via Kubernetes CronJob
- Backup script: `pg_dump` to persistent volume
- Retention: Keep last 30 days of backups
- Test restore procedures monthly
- Backup location: Separate PVC or external storage

**Database Migrations**:
- Run migrations in init container before application starts
- Migrations tracked in source control (Django migrations)
- Rollback strategy: Previous migration available in git history
- Zero-downtime migrations (add column nullable, then add constraint)

**Example Migration CronJob**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: jretirewise-db-backup
  namespace: jretirewise
spec:
  schedule: "2 0 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: jretirewise
          containers:
          - name: backup
            image: postgres:14
            command:
            - /bin/sh
            - -c
            - pg_dump -h postgresql -U $POSTGRES_USER $POSTGRES_DB | gzip > /backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: db-backups-pvc
```

### Logging & Monitoring

**Application Logging**:
- All logs to stdout (container best practice)
- Structured JSON logging with context (user ID, request ID, calculation ID)
- Log levels: DEBUG (dev), INFO (prod)
- OpenTelemetry collector sidecar (or external) for log aggregation
- Optional: Loki or ELK for log storage and querying

**Health Checks**:
- Readiness probe: `/health/ready` endpoint (checks DB, Redis, migrations)
- Liveness probe: `/health/live` endpoint (lightweight check)
- Startup probe: Wait for DB migrations to complete (Phase 2+)
- All probes include OpenTelemetry spans for observability

**Monitoring & Alerting**:
- Prometheus metrics endpoint: `/metrics`
- Key metrics:
  - HTTP request duration and status codes
  - Database query duration
  - Celery task execution time and success rate
  - Cache hit/miss rates
  - OpenTelemetry trace counts
- Optional alert rules (Phase 2+):
  - High error rate (>5% of requests)
  - Slow response times (p95 > 1s)
  - Failed calculations
  - Database connection pool exhaustion

### Scaling Considerations

**Horizontal Scaling** (Phase 2+):
- Application is stateless (suitable for horizontal scaling)
- Multiple Django replicas behind LoadBalancer Service
- Shared Redis for Celery task queue and caching
- PostgreSQL becomes bottleneck (consider read replicas in Phase 3)
- StatefulSet for PostgreSQL with replication

**Current Single-Instance Setup** (MVP):
- 1 Django replica (can increase for HA)
- 1 PostgreSQL instance with persistent volume
- 1 Redis instance for Celery and caching
- Simple but sufficient for home deployment

**Resource Limits** (MVP):
- Django: requests: 250m CPU, 512Mi RAM; limits: 500m CPU, 1Gi RAM
- PostgreSQL: requests: 250m CPU, 512Mi RAM; limits: 1000m CPU, 2Gi RAM
- Redis: requests: 100m CPU, 256Mi RAM; limits: 500m CPU, 512Mi RAM
- Adjust based on actual usage monitoring

### Security Best Practices

**Container Security**:
- Run as non-root user in Dockerfile
- Use read-only root filesystem (where possible)
- No privileged containers
- Image scanning for vulnerabilities (Phase 2+)
- Minimal base image (python:3.11-slim)

**Network Security**:
- NetworkPolicy to restrict traffic between pods
- TLS termination at Ingress
- HTTPS only (redirect HTTP → HTTPS)
- CSRF protection on all state-changing operations

**Secrets Management**:
- Never commit secrets to git
- Use Kubernetes Secrets (encrypted at rest)
- Rotate credentials periodically
- Audit secret access (optional advanced feature)

**RBAC (Role-Based Access Control)**:
- ServiceAccount for application with minimal permissions
- Separate accounts for different components (app, backup job)
- No cluster-admin role for application pods

### Disaster Recovery

**RTO/RPO Targets** (Recovery Time/Point Objectives):
- RTO: 30 minutes (restore application to working state)
- RPO: 24 hours (acceptable data loss = 1 day of backups)

**Disaster Recovery Procedures**:
1. **Application Failure**: ArgoCD detects unhealthy pods, auto-restarts
2. **Database Corruption**: Restore from most recent backup
3. **Pod Eviction**: Kubernetes reschedules pods automatically
4. **Node Failure**: Pods restart on healthy nodes (requires multi-node cluster for Phase 3)

**Testing**:
- Monthly: Test database restore procedures
- Quarterly: Full application failover test
- Document all recovery steps in runbook

### Upgrade & Rollback Strategy

**Zero-Downtime Upgrades**:
1. Push new image to Docker Hub
2. Update manifest repo (triggers ArgoCD)
3. Rolling update deploys new pods (1 at a time)
4. Old pods kept running until new pods are healthy
5. Health checks verify new version before removing old pods

**Automatic Rollback**:
- Smoke tests fail after deployment
- GitHub Actions automatically runs: `kubectl rollout undo deployment/jretirewise -n jretirewise`
- Alerts sent on rollback occurrence
- Manual investigation required to identify cause

**Manual Rollback** (if needed):
```bash
# List rollout history
kubectl rollout history deployment/jretirewise -n jretirewise

# Rollback to previous version
kubectl rollout undo deployment/jretirewise -n jretirewise

# Rollback to specific revision
kubectl rollout undo deployment/jretirewise -n jretirewise --to-revision=5
```

### Development & Staging Environments

**Current Setup** (Single Deployment):
- No separate staging environment initially (home setup)
- All testing done pre-deployment (unit, integration, E2E)
- Smoke tests run post-deployment against live app

**Future Enhancement** (Phase 3):
- Staging namespace for pre-production testing
- Automated promotion: Staging → Production
- Blue-green deployment with traffic switching

## Success Criteria

### MVP Phase
- [ ] Users can authenticate with Google OAuth
- [ ] Users can input financial data (assets, income, expenses)
- [ ] 4% and 4.7% calculators produce correct output
- [ ] Results persist to PostgreSQL
- [ ] Frontend displays results with basic charts
- [ ] Application deploys to Kubernetes cluster
- [ ] OpenTelemetry logs calculations and API calls
- [ ] Full test coverage of calculation engines
- [ ] API documentation complete

### Phase 2
- [ ] Monte Carlo simulator runs and produces probability distributions
- [ ] Historical analysis works against 60+ years of data
- [ ] Async calculations show progress to user
- [ ] Scenario comparison displays correctly
- [ ] Performance acceptable for 100k iteration Monte Carlo (<30 seconds)

### Phase 3
- [ ] Professional-grade features implemented
- [ ] User documentation complete
- [ ] UI polished and responsive
- [ ] Advanced observability operational

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Complex financial calculations | High | Use established libraries (NumPy, Pandas), validate against Bogleheads/FIREcalc |
| Performance on large Monte Carlo runs | Medium | Implement async processing, set iteration limits, cache results |
| Google OAuth integration issues | Medium | Use well-tested libraries (django-allauth), test thoroughly |
| PostgreSQL data loss | High | Implement automated backups, test restore procedures |
| Kubernetes cluster failures | Medium | Keep single-instance acceptable per requirements; add redundancy in Phase 3 |
| Security vulnerabilities | High | Follow OWASP guidelines, regular dependency updates, security scanning in CI/CD |
| Poor UX for chart-heavy interface | Medium | Iterate based on user feedback, follow industry standards (Bogleheads, etc.) |

## Timeline Summary

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 (MVP) | 8-12 weeks | Core platform, basic calculations, authentication |
| Phase 2 | 6-8 weeks | Advanced calculations, async processing, visualization |
| Phase 3 | 4-6 weeks | Professional features, optimization, polish |
| **Total** | **18-26 weeks** | **Production-ready retirement planning platform** |

## Next Steps

1. Review this plan and provide feedback
2. Clarify any specific requirements or constraints
3. Confirm technology choices and architecture
4. Once approved, begin Phase 1 implementation
5. Create detailed task breakdown for Phase 1
6. Set up development environment and repositories
