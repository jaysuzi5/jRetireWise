# GitHub Actions CI/CD Pipeline

## Overview

The jRetireWise project uses GitHub Actions to implement a comprehensive CI/CD pipeline that automates testing, building, and deployment of the application.

## Pipeline Architecture

```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ├─► ┌───────────────┐
       │   │ Test Job      │ ◄─ Run unit & integration tests
       │   │ (Always runs) │    Check coverage
       │   └───────────────┘
       │
       ├─► ┌───────────────┐
       │   │ Lint Job      │ ◄─ Code quality checks
       │   │ (Always runs) │    Black, isort, flake8
       │   └───────────────┘
       │
       └─► ┌───────────────┐     ┌─────────────────┐
           │ Build Job     │────►│ Push to Docker  │ ◄─ On main/develop
           │ (If tests     │     │ Hub             │
           │  pass)        │     └─────────────────┘
           └───────────────┘
                  │
                  └─► ┌───────────────┐     ┌──────────────────┐
                      │ Deploy Job    │────►│ Sync ArgoCD App  │ ◄─ On main branch
                      │ (If build OK) │     │ Trigger K8s      │
                      └───────────────┘     └──────────────────┘
                              │
                              └─► ┌───────────────┐
                                  │ E2E Tests     │ ◄─ Browser tests
                                  │ (Optional)    │    Smoke tests
                                  └───────────────┘
```

## Workflows

### 1. Test Workflow (`test.yml`)

**Triggered on**: Push to any branch, Pull requests

**Purpose**: Fast feedback on code quality and test coverage

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

**Jobs**:
1. **Unit Tests** - Form validation tests in isolation
   - Runs: `pytest tests/unit/test_forms.py`
   - Should complete in <1 minute

2. **Integration Tests** - Full request/response cycle
   - Runs: `pytest tests/integration/`
   - Tests database interactions
   - Should complete in <3 minutes

3. **Coverage Report** - Code coverage metrics
   - Uploads to Codecov
   - Fails if coverage drops below minimum

**Example output**:
```
PASSED tests/unit/test_forms.py::FinancialProfileFormTestCase::test_profile_form_saves_correctly
PASSED tests/integration/test_profile_views.py::ProfileViewIntegrationTestCase::test_create_new_profile
======================== 34 passed in 5.7s ========================
Coverage: 74%
```

### 2. CI/CD Workflow (`ci-cd.yml`)

**Triggered on**: Push to main/develop, Manual trigger

**Purpose**: Complete pipeline from code to production

#### Test Job
- Same as test.yml workflow
- Uploads coverage to Codecov
- Fails on test failures

#### Lint Job
- **Black**: Code formatting checks
- **isort**: Import ordering
- **flake8**: PEP8 style
- **bandit**: Security vulnerability scanning

#### Build Job
**Triggered if**: test and lint succeed, AND pushing to main/develop

- **Builds** Docker image with Buildx (multi-platform)
- **Pushes** to Docker Hub with semantic versioning:
  - `yourusername/jretirewise:main` (latest commit on main)
  - `yourusername/jretirewise:develop` (latest commit on develop)
  - `yourusername/jretirewise:v1.2.3` (tagged releases)
  - `yourusername/jretirewise:latest` (main branch only)

**Image cache**: Uses GitHub Actions cache for faster builds

#### Deploy Job
**Triggered if**: build succeeds AND on main branch only

- **Syncs** ArgoCD application to Kubernetes
- **Health checks** against production URL
- **Smoke tests** to verify deployment success
- **Slack notification** of deployment status

#### E2E Tests Job
**Triggered if**: build succeeds AND on main branch

- Runs Playwright E2E tests
- Validates complete user workflows
- Captures screenshots on failure

## Environment Variables & Secrets

### Required Secrets

Add these to GitHub repository settings (Settings > Secrets and variables):

```
DOCKER_USERNAME       # Docker Hub username
DOCKER_PASSWORD       # Docker Hub access token
ARGOCD_SERVER         # ArgoCD server URL (e.g., argocd.example.com)
ARGOCD_AUTH_TOKEN     # ArgoCD API token
SLACK_WEBHOOK_URL     # Slack webhook for notifications (optional)
```

### Configuration Variables

Add these to repository variables (Settings > Variables):

```
REGISTRY              # Docker registry (docker.io)
IMAGE_NAME            # Image path (username/jretirewise)
```

## Setup Instructions

### 1. Configure Docker Hub

```bash
# Create Docker Hub access token
# Go to docker.com > Account > Security > New Access Token

# Add secrets to GitHub
gh secret set DOCKER_USERNAME -b yourusername
gh secret set DOCKER_PASSWORD -b your_access_token
```

### 2. Configure ArgoCD (for production deployment)

```bash
# Create ArgoCD API token
argocd account generate-token

# Create ArgoCD app (if not exists)
argocd app create jretirewise-prod \
  --repo https://github.com/yourusername/jretirewise \
  --path k8s/overlays/prod \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace jretirewise-prod

# Add secrets to GitHub
gh secret set ARGOCD_SERVER -b "your-argocd-server.com"
gh secret set ARGOCD_AUTH_TOKEN -b "your_argocd_token"
```

### 3. Configure Slack Notifications (optional)

```bash
# Create Slack webhook
# Go to slack.com > Your Apps > Create New App > Incoming Webhooks

gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/..."
```

## Viewing Pipeline Results

### In GitHub UI

1. Go to repository > Actions tab
2. Click on workflow run to view details
3. Expand job to see logs and artifacts

### PR Checks

Status checks appear on pull requests:
- ✅ All checks must pass before merging
- ❌ Failed checks block merge
- ⏳ Pending checks require waiting

### Coverage Reports

Coverage reports are uploaded to [Codecov](https://codecov.io/):
1. Link your GitHub repo to Codecov
2. View coverage trends and file-by-file coverage

## Deployment Flow

### Development Deployment (develop branch)

```
Push to develop → Test → Lint → Build → Push to Docker Hub:develop
                                         ├─ Image ready for manual testing
                                         └─ No automatic K8s deployment
```

### Production Deployment (main branch)

```
Push to main → Test → Lint → Build → Sync ArgoCD → K8s Deployment
              (must pass)         │                    │
                                 └─ Push to          └─ Health check
                                   Docker Hub          Smoke test
                                   (with latest tag)   Slack notify
```

### Manual Deployments

```
GitHub Actions > ci-cd workflow > Run workflow > Select branch
```

## Testing Locally Before Pushing

### Run Tests Locally

```bash
# Install test dependencies
pip install -r requirements.txt

# Run unit tests
pytest tests/unit/test_forms.py -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/unit/ tests/integration/ --cov=jretirewise --cov-report=html
```

### Run Linting Locally

```bash
# Install linting tools
pip install black flake8 isort pylint bandit

# Format code with Black
black .

# Check imports with isort
isort .

# Run flake8
flake8 . --exclude=migrations,venv,__pycache__

# Security scan
bandit -r jretirewise --skip B101,B601
```

### Build Docker Image Locally

```bash
# Build image
docker build -t jretirewise:local .

# Test image
docker run -it jretirewise:local python manage.py shell
```

## Troubleshooting

### Tests Failing

1. Check GitHub Actions logs (Actions > Workflow > Job > Logs)
2. Reproduce locally with same Python version:
   ```bash
   python --version  # Should be 3.11
   pip install -r requirements.txt
   pytest tests/ -v
   ```
3. Check for flaky tests (timing issues, state pollution)

### Docker Build Failing

1. Check Dockerfile syntax
   ```bash
   docker build -t jretirewise:test .
   ```
2. Verify all dependencies are in requirements.txt
3. Check Docker Hub credentials and registry access

### ArgoCD Deployment Failing

1. Verify ArgoCD is accessible:
   ```bash
   argocd app get jretirewise-prod
   ```
2. Check K8s manifest syntax:
   ```bash
   kubectl kustomize k8s/overlays/prod | kubectl apply --dry-run=client -f -
   ```
3. Review ArgoCD app logs:
   ```bash
   kubectl logs -n argocd deployment/argocd-application-controller
   ```

### Health Check Failing

1. Check if application is responding:
   ```bash
   curl -v https://jretirewise.example.com/health/ready/
   ```
2. Check Ingress status:
   ```bash
   kubectl get ingress -n jretirewise-prod
   kubectl describe ingress jretirewise -n jretirewise-prod
   ```
3. Check pod logs:
   ```bash
   kubectl logs -f deployment/prod-jretirewise-web -n jretirewise-prod
   ```

## Monitoring & Alerts

### GitHub Actions Status

- **Status badge**: Add to README.md
  ```markdown
  ![Tests](https://github.com/yourusername/jretirewise/workflows/Tests/badge.svg)
  ![CI/CD](https://github.com/yourusername/jretirewise/workflows/CI%2FCD%20Pipeline/badge.svg)
  ```

### Slack Notifications

Deploy job sends Slack notifications on:
- ✅ Successful deployment
- ❌ Failed deployment
- Can be extended to notify on test failures

### Email Notifications

GitHub Actions sends email on:
- Workflow failures (configurable in GitHub settings)
- Branch push (if you enable it)

## Cost Considerations

GitHub Actions pricing:
- **Free tier**: 2,000 minutes/month for private repos
- **Beyond free**: $0.008 per minute

Optimization:
- Skip expensive jobs (tests run on every push, build only on main/develop)
- Use caching for dependencies (pip, Docker layers)
- Run jobs in parallel where possible
- Skip jobs for non-code changes (README, docs)

```yaml
# Skip CI for documentation changes
if: "!contains(github.event.head_commit.message, '[skip ci]')"
```

## Advanced Topics

### Matrix Builds

Test against multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
  - uses: actions/setup-python@v4
    with:
      python-version: ${{ matrix.python-version }}
```

### Conditional Steps

```yaml
- name: Deploy to prod
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: kubectl apply -k k8s/overlays/prod
```

### Reusable Workflows

Create shared workflows in `.github/workflows/`:

```yaml
# .github/workflows/shared-test.yml
name: Shared Test Workflow
on:
  workflow_call

jobs:
  test:
    runs-on: ubuntu-latest
    # ... test steps
```

Then call from other workflows:

```yaml
uses: ./.github/workflows/shared-test.yml
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [ArgoCD CLI Documentation](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_login/)
- [Codecov GitHub Integration](https://docs.codecov.com/docs)
