# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**jRetireWise** is a professional retirement planning calculator application that enables users to track financial information, model retirement scenarios, and make data-driven retirement decisions. It supports deterministic rules (4% rule, 4.7% rule) and sophisticated stochastic simulations (Monte Carlo, sensitivity analysis, historical period analysis).

**Status**: Planning phase complete. Refer to `documents/plan.md` for the comprehensive development roadmap.

## Technology Stack

- **Backend**: Python 3.11+ with Django 5.0+ and Django REST Framework
- **Frontend**: Django templates with HTMX, Chart.js, Tailwind CSS
- **Database**: PostgreSQL 14+
- **Task Queue**: Celery with Redis broker
- **Container**: Docker, Kubernetes (home cluster deployment)
- **CI/CD**: GitHub Actions with Docker Hub and ArgoCD integration
- **Observability**: OpenTelemetry with local collector integration

## Architecture

The application follows a unified Django architecture:
- **View Layer**: Django templates + DRF for API endpoints
- **Business Logic**: Calculation engines (4%, 4.7%, Monte Carlo, historical analysis)
- **Database Models**: User, Asset, Scenario, CalculationResult, FinancialProfile
- **Async Processing**: Celery tasks for long-running calculations
- **Frontend**: Server-rendered templates with HTMX for dynamic interactions

See `documents/plan.md` - **Architecture Overview** section for detailed system design.

## Development Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### Running
```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (in another terminal)
celery -A config worker -l info

# Collect static files
python manage.py collectstatic

# Access application at http://localhost:8000
```

### Testing (See Testing Strategy in plan.md)
```bash
# Unit tests
pytest tests/unit/ --cov=jretirewise --cov-fail-under=80

# Integration tests
pytest tests/integration/ -v

# UI/E2E smoke tests
pytest tests/e2e/smoke/ -v

# All tests
pytest tests/

# Specific test file
pytest tests/unit/calculations/test_four_percent_calculator.py

# With HTML coverage report
pytest --cov=jretirewise --cov-report=html
```

### Code Quality
```bash
# Lint with flake8
flake8 jretirewise tests

# Format with black
black jretirewise tests

# Type checking (if using mypy)
mypy jretirewise
```

## Docker & Deployment

### Local Docker Compose
```bash
docker-compose up --build
# Access at http://localhost:8000
```

### Building Docker Image
```bash
docker build -t dockerhubuser/jretirewise:v1.0.0 .
docker push dockerhubuser/jretirewise:v1.0.0
```

### Kubernetes Deployment
Deployment is managed via ArgoCD monitoring a separate manifests repository. See `documents/plan.md` - **Deployment & DevOps** section for:
- CI/CD pipeline details
- Docker Hub publishing
- ArgoCD integration
- Database backup strategy
- Health checks and monitoring
- Security best practices
- Disaster recovery procedures

## Project Structure

```
jretirewise/
├── config/                 # Django settings and URLs
├── jretirewise/           # Main application package
│   ├── authentication/    # Google OAuth, user models
│   ├── financial/         # Financial data models and serializers
│   ├── calculations/      # Calculation engines (4%, 4.7%, Monte Carlo, etc.)
│   ├── scenarios/         # Scenario models and management
│   ├── api/               # DRF API views and endpoints
│   └── templates/         # Django templates
├── tests/
│   ├── unit/              # Unit tests (70% of tests)
│   ├── integration/       # Integration tests (20% of tests)
│   └── e2e/               # UI/E2E tests with Playwright (10% of tests)
├── static/                # CSS, JavaScript, images
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Local development stack
└── requirements.txt       # Python dependencies
```

## Testing Strategy

**All phases require passing tests before code merge and deployment.**

See `documents/plan.md` - **Testing Strategy** section for comprehensive details including:
- Unit tests (pytest, ≥80% coverage)
- Integration tests (pytest-django, DRF testing)
- UI/E2E tests (Playwright browser automation)
- Test fixtures and factory patterns
- CI/CD integration with GitHub Actions
- Post-deployment smoke tests with automatic rollback

**Quick Reference**:
- Unit test target: ≥80% coverage
- Calculation engines: 100% coverage
- API views: ≥75% coverage
- Integration tests: MVP 10+, Phase 2 20+, Phase 3 30+
- E2E/Smoke tests: MVP 5+, Phase 2 10+, Phase 3 15+

## Phase Roadmap

See `documents/plan.md` for detailed phase planning:

1. **Phase 1 (MVP)** - 8-12 weeks
   - Google OAuth authentication
   - Financial data management (assets, income, expenses)
   - 4% and 4.7% rule calculators
   - Scenario management
   - Basic visualization (Chart.js)
   - Kubernetes deployment
   - Complete test coverage

2. **Phase 2** - 6-8 weeks
   - Monte Carlo simulations (1k-100k iterations)
   - Historical period backtesting
   - Async calculation processing (Celery)
   - Advanced charting (confidence bands, heatmaps)
   - Scenario comparison
   - PDF/CSV export

3. **Phase 3** - 4-6 weeks
   - Professional features (Social Security, healthcare, inflation)
   - Comprehensive reporting
   - Performance optimization
   - Advanced observability
   - UI polish and accessibility

## Key Development Areas

### Calculation Engines
- Location: `jretirewise/calculations/`
- Unit test coverage: 100% required
- Reference: `documents/plan.md` - **Calculation Engines**

### API Endpoints
- Location: `jretirewise/api/views.py`
- Integration test coverage: ≥75%
- Framework: Django REST Framework

### Database Models
- Location: `jretirewise/financial/models.py`, `scenarios/models.py`
- Include: User, Asset, Scenario, CalculationResult, FinancialProfile
- Use Django ORM and migrations

### Frontend Templates
- Location: `jretirewise/templates/`
- Framework: Django templates with HTMX
- Styling: Tailwind CSS
- Charts: Chart.js (vanilla JavaScript)
- Light interactivity: Alpinejs

### Authentication
- Method: Google OAuth 2.0 (via django-allauth)
- Sessions: HTTP-only cookies with CSRF protection
- API Auth: Token-based for AJAX requests

## Database

**PostgreSQL 14+** with:
- Automated daily backups via Kubernetes CronJob
- Migrations in source control (Django migrations)
- Init container runs migrations before app startup
- Zero-downtime migration strategy

See `documents/plan.md` - **Database Management** for backup and migration strategies.

## Observability

**OpenTelemetry** integration for:
- HTTP request spans (latency, status)
- Database query spans
- Celery task execution spans
- Custom financial calculation metrics
- Structured JSON logging with context

Collector configuration: Local collector for development, external collector for production.

## CI/CD Pipeline

**GitHub Actions** workflow:
1. **PR checks**: Unit tests → Integration tests → Linting → E2E tests
2. **Merge to main**: Build image → Push to Docker Hub → Update manifests → Trigger ArgoCD
3. **Post-deployment**: Run smoke tests → Auto-rollback on failure

Details: `documents/plan.md` - **CI/CD Pipeline**

## Deployment Strategy

- **Container**: Single Dockerfile for unified Django app
- **Registry**: Docker Hub with semantic versioning
- **Orchestration**: Kubernetes on home cluster
- **GitOps**: ArgoCD monitors manifest repository
- **Upgrade**: Zero-downtime rolling updates
- **Rollback**: Automatic on smoke test failure, manual with kubectl commands

## Security Considerations

- Container: Non-root user, read-only filesystem where possible
- Network: NetworkPolicy, TLS at Ingress, HTTPS-only
- Secrets: Kubernetes Secrets (encrypted), never in git
- RBAC: ServiceAccount with minimal permissions
- OAuth: Google OAuth 2.0 for user authentication

See `documents/plan.md` - **Security Best Practices** for details.

## Documentation Reference

For comprehensive information on any aspect, refer to `documents/plan.md`:

- **Architecture**: High-level system design, data models, components
- **Implementation Phases**: Detailed breakdown of MVP and enhancement phases
- **Testing Strategy**: Complete testing approach, pytest configuration
- **Deployment & DevOps**: CI/CD, Docker, Kubernetes, backups, monitoring
- **Risk Mitigation**: Identified risks and mitigation strategies
- **Success Criteria**: Measurable deliverables for each phase

## Documentation Standards

**All documentation should be organized under the `documents/` directory following this structure:**

```
documents/
├── Phase_1_MVP/                 # Phase 1 documentation
│   ├── Phase_1_MVP.md          # Main requirements checklist
│   ├── README.md               # Quick reference guide
│   └── supporting/             # Supporting documentation
│       ├── TEST_REPORT.md
│       ├── KUBERNETES.md
│       ├── CI_CD.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── PHASE_1_COMPLETION_SUMMARY.txt
├── Phase_2_**/                  # Phase 2 documentation (similar structure)
├── Phase_3_**/                  # Phase 3 documentation (similar structure)
├── test_results/                # Test result archives
│   ├── 202511301145_test_results.md
│   ├── 202511302100_test_results.md
│   └── ...                      # One file per test run (YYYYMMDDHHmm format)
├── plan.md                      # Complete project roadmap
└── [other docs]                 # Additional documentation
```

**Guidelines:**
- All documentation should be in `documents/` directory, not in root
- Organize by phase or functional area in subdirectories
- Each phase should have a main README and supporting/ subdirectory
- Test results should have timestamped filenames: `YYYYMMDDHHmm_test_results.md`
- Use Markdown format for all documentation files

## Testing & Test Reporting Standards

**CRITICAL: Every code change must include updated test cases and a test result summary.**

### Test-Driven Development Workflow

1. **Make Code Changes**
   - Modify code in the application

2. **Update Test Cases**
   - Add/update unit tests in `tests/unit/`
   - Add/update integration tests in `tests/integration/`
   - Add/update E2E tests in `tests/e2e/`

3. **Run All Tests**
   ```bash
   # Via Docker (recommended)
   docker-compose exec -T web pytest tests/unit/test_forms.py tests/integration/ -v

   # Or locally with pytest
   pytest tests/ -v --cov=jretirewise --cov-report=term-missing
   ```

4. **Create Test Summary Document**
   - Create file: `documents/test_results/YYYYMMDDHHmm_test_results.md`
   - Example: `documents/test_results/202511301145_test_results.md`
   - Replace YYYYMMDDHHmm with current year, month, day, hour, minute

5. **Test Summary Format**
   ```markdown
   # Test Results Report
   **Test Run Date/Time**: YYYY-MM-DD HH:MM:SS (UTC-5)
   **Test Types**: Unit Tests, Integration Tests, E2E Tests

   ## Executive Summary

   ✅ ALL TESTS PASSED - X/X tests successful (100%)

   | Metric | Result |
   |--------|--------|
   | **Total Tests Run** | X |
   | **Tests Passed** | X (100%) |
   | **Tests Failed** | 0 (0%) |
   | **Code Coverage** | XX% |
   | **Execution Time** | X.XX seconds |
   | **Status** | ✅ PASS / ❌ FAIL |

   ## Test Breakdown

   ### Unit Tests (X/X passed)
   - Test file: tests/unit/
   - Coverage: XX%

   ### Integration Tests (X/X passed)
   - Test file: tests/integration/
   - Coverage: XX%

   ## Code Coverage Details

   | Module | Coverage |
   |--------|----------|
   | module1 | XX% |
   | module2 | XX% |

   ## Issues Found
   - ✅ No issues

   ## Recommendations
   - Ready for deployment
   ```

### Test Coverage Requirements

- **Unit Tests**: ≥80% coverage (70%+ minimum)
- **Integration Tests**: ≥75% coverage
- **Calculation Engines**: 100% coverage required
- **Overall**: Must meet or exceed requirements before committing

### Example Test Workflow

```bash
# 1. Make code changes
# [Edit files]

# 2. Run tests
docker-compose exec -T web pytest tests/ -v --cov=jretirewise --cov-report=term-missing

# 3. If tests fail, fix code and re-run
# [Fix issues]
docker-compose exec -T web pytest tests/ -v

# 4. Create test results document
# Create documents/test_results/202511301200_test_results.md with summary

# 5. Commit changes
git add .
git commit -m "feat: Add new feature with comprehensive tests"

# 6. Push to GitHub
git push origin feature-branch
```

## Common Development Workflows

### Adding a New Calculator
1. Create calculator class in `jretirewise/calculations/`
2. Write 100% unit tests in `tests/unit/calculations/`
3. Create DRF endpoint in `jretirewise/api/views.py`
4. Write integration tests for endpoint
5. Add template/HTMX interaction
6. Run full test suite: `pytest tests/` - all must pass
7. Create test summary: `documents/test_results/YYYYMMDDHHmm_test_results.md`
8. Commit with test results documentation

### Adding a New Model
1. Define model in appropriate app (`financial/`, `scenarios/`, etc.)
2. Create migrations: `python manage.py makemigrations`
3. Write model tests in `tests/integration/models/`
4. Create serializers in `jretirewise/api/serializers.py`
5. Write API endpoint tests
6. Run all tests and verify coverage
7. Create test summary document
8. Update CLAUDE.md if impacts architecture

### Fixing a Bug
1. Write test case that reproduces the bug (test should fail initially)
2. Fix the bug in code
3. Verify test now passes
4. Run full test suite to ensure no regressions
5. Create test summary showing all tests pass
6. Commit with test results

### Deployment
1. Make code changes with comprehensive tests
2. Run full test suite and generate test summary
3. Commit to feature branch with test results
4. Create PR (GitHub Actions runs checks)
5. Merge to main (triggers Docker build and ArgoCD)
6. Post-deployment smoke tests validate deployment
7. If tests fail, automatic rollback occurs

## Helpful Resources

- **Calculation Reference**: Bogleheads, FIREcalc, early retirement forums
- **Django**: https://docs.djangoproject.com/
- **DRF**: https://www.django-rest-framework.org/
- **Celery**: https://docs.celeryproject.org/
- **Kubernetes**: https://kubernetes.io/docs/
- **ArgoCD**: https://argo-cd.readthedocs.io/
- **Playwright**: https://playwright.dev/python/

## Contact & Support

For questions about the development plan, refer to `documents/plan.md`. Future instances of Claude Code will use this file to understand the architecture and development practices.
