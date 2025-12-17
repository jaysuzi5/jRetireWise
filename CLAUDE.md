# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**jRetireWise** is a professional retirement planning calculator application that enables users to track financial information, model retirement scenarios, and make data-driven retirement decisions. It supports deterministic rules (4% rule, 4.7% rule) and sophisticated stochastic simulations (Monte Carlo, sensitivity analysis, historical period analysis).

**Status**: Planning phase complete. Refer to `documents/plan.md` for the comprehensive development roadmap.

## Project Mode & Development Philosophy

**⚠️ EXPERIMENTAL PROJECT - AUTONOMOUS MODE ENABLED**

This is an experimental project being developed in close-to-production mode with the following characteristics:

✅ **Fully Backed Up in GitHub**
- All code is continuously backed up to GitHub repository
- All commits are pushed to feature branch `01_initial_implementation`
- Complete version history maintained
- Easy rollback capability if needed
- No code is lost - everything is recoverable from GitHub

✅ **Comfortable with Autonomous Decision-Making**
- You (Claude Code) are encouraged to make decisions and implement recommendations without excessive prompting
- Do not ask for permission for obvious improvements or best practices
- Do not ask for approval on standard refactoring or cleanup
- Do not require confirmation for test-driven development and coverage verification
- Proceed with quality-focused changes confidently
- Implement changes directly without asking "Should I proceed?" or "Would you like me to...?"
- Make judgment calls on code improvements, refactoring, and testing without seeking approval
- Only ask when truly ambiguous or when multiple significantly different approaches exist

✅ **High-Risk Tolerance Mode**
- This is an experimental/learning project
- Testing is comprehensive (unit, integration, E2E)
- All changes are tracked in git with detailed commit messages
- All changes include test results documentation
- Full recovery capability via GitHub if issues arise
- You may take calculated risks on new patterns or approaches
- Experimental features and optimizations are encouraged

✅ **Operating Guidelines for Autonomous Mode**
1. **Make decisions based on best practices** - Don't ask, implement
2. **Implement improvements proactively** - See a better way? Do it
3. **Refactor confidently** - Code quality improvements don't need approval
4. **Test thoroughly** - All changes must have tests and test results
5. **Document decisions** - Explain in commit messages why changes were made
6. **Commit frequently** - Keep git history clean and detailed
7. **Push to GitHub regularly** - Ensure backups are current
8. **Error recovery** - If something breaks, use git to revert and re-approach

## 🔴 CRITICAL: Git Branch Workflow

**⚠️ NEVER COMMIT CODE DIRECTLY TO THE MAIN BRANCH**

### Mandatory Workflow
1. **Always create feature branch first** - Format: `{phase}_{description}` (e.g., `02_1_advanced_calculation_engines`)
2. **All development on feature branch** - Every commit to feature branch
3. **Test on feature branch** - All tests must pass before merge
4. **Merge only when validated** - Feature branch → main (via fast-forward or merge commit)
5. **Push to GitHub after merge** - Triggers CI/CD pipeline

### Process
```bash
# WRONG - Never do this:
git checkout main
git add . && git commit -m "message"  # ❌ WRONG

# RIGHT - Always do this:
git checkout -b 02_1_feature_name     # Create feature branch
git add . && git commit -m "message"  # Commit to feature branch
git push origin 02_1_feature_name     # Push feature branch
# Test and validate...
git checkout main
git pull origin main                  # Ensure main is up to date
git merge 02_1_feature_name           # Merge feature → main
git push origin main                  # Push to GitHub (triggers CI/CD)
```

### Why This Matters
- ✅ Feature branches allow isolated development
- ✅ Main branch stays clean and deployable
- ✅ Easy to revert entire features if needed
- ✅ CI/CD pipeline only triggered on main changes
- ✅ Clear history of feature implementations
- ✅ Prevents accidental breaking changes to production

### Examples Done Wrong (Learn from Mistakes)
- ❌ Phase 2.1: Code was committed to main instead of feature branch
  - Should have stayed on `02_1_Advanced_Calculation_Engines` branch
  - Merged to main only after all validation complete
  - This is now corrected for future phases

✅ **When to Still Communicate**
- Only when you genuinely cannot determine the best path forward
- When there are multiple equally valid architectural approaches with significant tradeoffs
- When the decision would substantially impact the user's workflow or expectations
- When you lack critical information to proceed (e.g., unclear requirements or external dependencies)
- Avoid asking for confirmation on standard decisions - just implement and explain in the commit message

✅ **GitHub as Safety Net**
- Every commit is backed up immediately
- No need to ask permission for significant changes
- No need to ask permission for experimental approaches
- No need to ask permission for refactoring
- GitHub history provides complete audit trail
- Easy recovery from any mistakes via `git revert` or rollback

**Bottom Line**: You have permission to work autonomously, make confident decisions, implement improvements proactively, and experiment with better approaches. GitHub provides the safety net. Testing and documentation provide quality assurance. Trust the process.

## Technology Stack

- **Backend**: Python 3.11+ with Django 5.0+ and Django REST Framework
- **Frontend**: Django templates with HTMX, Chart.js, Tailwind CSS
- **Database**: PostgreSQL 14+
- **Container**: Docker, Kubernetes (home cluster deployment)
- **CI/CD**: GitHub Actions with Docker Hub and ArgoCD integration
- **Observability**: OpenTelemetry with local collector integration

## Architecture

The application follows a unified Django architecture:
- **View Layer**: Django templates + DRF for API endpoints
- **Business Logic**: Calculation engines (4%, 4.7%, Monte Carlo, historical analysis)
- **Database Models**: User, Asset, Scenario, CalculationResult, FinancialProfile
- **Calculation Processing**: Synchronous calculations via Django signals (no task queue needed)
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

# Collect static files
python manage.py collectstatic

# Access application at http://localhost:8000
```

### Testing (See Testing Strategy in plan.md)
```bash
# Unit tests
pytest tests/unit/ --cov=jretirewise --cov-fail-under=85

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
- Unit test target: ≥85% coverage
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
- Secrets: Sealed Secrets (SealedSecret CRD), never plaintext in git
- RBAC: ServiceAccount with minimal permissions
- OAuth: Google OAuth 2.0 for user authentication

See `documents/plan.md` - **Security Best Practices** for details.

### Kubernetes Secrets Management

**CRITICAL RULE**: Never commit plaintext Kubernetes Secrets to the repository. Always use Sealed Secrets.

#### What are Sealed Secrets?

Sealed Secrets encrypt sensitive data with a cluster-specific sealing key, allowing you to safely commit encrypted secrets to git while keeping the actual values secure.

#### Workflow for Managing Secrets

1. **Install kubeseal** on your local machine:
   ```bash
   # macOS
   brew install kubeseal

   # Or download from: https://github.com/bitnami-labs/sealed-secrets/releases
   ```

2. **Create or update a secret:**
   ```bash
   # Create a temporary plaintext secret file (temp.yaml)
   cat > temp.yaml << 'EOF'
   apiVersion: v1
   kind: Secret
   metadata:
     name: jretirewise-secret
   type: Opaque
   stringData:
     SECRET_KEY: "your-actual-secret-key"
     DATABASE_PASSWORD: "your-actual-db-password"
     # ... other secrets
   EOF
   ```

3. **Seal the secret:**
   ```bash
   kubeseal --controller-namespace kube-system --format yaml < temp.yaml > secret.yaml
   ```

   This command:
   - Reads the plaintext secret from `temp.yaml`
   - Encrypts it using the cluster's sealing key (from `kube-system` namespace)
   - Outputs the encrypted SealedSecret to `secret.yaml`

4. **Clean up and commit:**
   ```bash
   rm temp.yaml  # Delete the plaintext version
   git add k8s/base/secret.yaml
   git commit -m "chore: Update sealed secrets"
   git push origin main
   ```

5. **Deploy to cluster:**
   ```bash
   kubectl apply -f k8s/base/secret.yaml

   # Verify the sealed secret was decrypted correctly
   kubectl get secret jretirewise-secret -o yaml
   ```

#### Viewing Secrets in the Cluster

Only the cluster with the matching sealing key can decrypt sealed secrets:

```bash
# View encrypted (sealed) version in git - safe to commit
cat k8s/base/secret.yaml

# View decrypted (plaintext) version on the cluster - only works in-cluster
kubectl get secret jretirewise-secret -o yaml
```

#### Updating Individual Secrets

If you need to update just one secret value:

```bash
# Create a temp secret with ONLY the value you want to update
cat > temp.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: jretirewise-secret
type: Opaque
stringData:
  SECRET_KEY: "new-secret-key-value"
EOF

# Seal it
kubeseal --controller-namespace kube-system --format yaml < temp.yaml > secret.yaml

# Replace the encryptedData value in k8s/base/secret.yaml with the new encrypted value
rm temp.yaml
```

#### Important Notes

- **Sealing key location**: `kube-system` namespace (standard for kubeseal)
- **Format flag**: Always use `--format yaml` for YAML output
- **Cluster-specific**: Each cluster has its own sealing key - sealed secrets from one cluster cannot be decrypted on another
- **Never commit plaintext**: The `temp.yaml` file should NEVER be committed to git
- **Local development**: For local development, use an unencrypted local k8s/base/secret.yaml (add to .gitignore)

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

- **Unit Tests**: ≥85% coverage (target for all new code)
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
- **Kubernetes**: https://kubernetes.io/docs/
- **ArgoCD**: https://argo-cd.readthedocs.io/
- **Playwright**: https://playwright.dev/python/

## Contact & Support

For questions about the development plan, refer to `documents/plan.md`. Future instances of Claude Code will use this file to understand the architecture and development practices.
