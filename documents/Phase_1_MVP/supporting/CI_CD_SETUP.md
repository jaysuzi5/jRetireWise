# CI/CD Pipeline Setup Guide

This document outlines all the setup required to make the GitHub Actions CI/CD pipeline fully functional.

## Pipeline Overview

The CI/CD pipeline (`.github/workflows/ci-cd.yml`) performs the following steps:

1. **Test**: Runs unit and integration tests (triggers on all push/PR to main and develop)
2. **Lint**: Code quality checks (triggers on all push/PR to main and develop)
3. **Build**: Creates and pushes Docker image to Docker Hub (triggers on push to main/develop after test+lint pass)
4. **Deploy**: Deploys to Kubernetes via ArgoCD (triggers on push to main only after build passes)
5. **E2E**: Runs end-to-end tests (triggers on push to main after build)

## Required Setup

### 1. Docker Hub Account

**What you need:**
- Docker Hub account (free tier is fine)
- Docker username and access token

**Steps to create Docker Hub token:**

1. Go to https://hub.docker.com/settings/security/tokens
2. Create a new access token with read/write permissions
3. Note the token (you'll use it below)

**Information needed from you:**
- Docker Hub username
- Docker Hub access token

---

### 2. GitHub Repository Secrets

Add the following secrets to your GitHub repository:

**Location:** Settings → Secrets and variables → Actions

#### 2.1 Docker Credentials (Required for Build job)

```
DOCKER_USERNAME: <your-docker-hub-username>
DOCKER_PASSWORD: <your-docker-hub-access-token>
```

**Purpose**: Authenticate with Docker Hub to push images

---

### 3. ArgoCD Setup (Required for Deploy job)

The deploy job uses ArgoCD to manage Kubernetes deployments. This requires:

#### 3.1 ArgoCD Installation

Install ArgoCD in your Kubernetes cluster:

```bash
# Create argocd namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

#### 3.2 ArgoCD Configuration

1. Access ArgoCD UI:
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   # Then visit https://localhost:8080
   ```

2. Login with username `admin` and the password from above

3. Create a new repository credential:
   - Go to Settings → Repositories
   - Click "Connect Repo"
   - Use GitHub credentials to authenticate your manifests repository

#### 3.3 Create ArgoCD Application

Create an ArgoCD Application for jRetireWise:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jretirewise-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/<your-manifests-repo>
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: jretirewise
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

#### 3.4 GitHub Secrets for ArgoCD

Add these secrets to GitHub:

```
ARGOCD_SERVER: <your-argocd-server-url>
  Example: argocd.yourdomain.com or your-k8s-cluster-ip:6443

ARGOCD_AUTH_TOKEN: <your-argocd-admin-token>
```

**How to get ArgoCD auth token:**

```bash
# Login to ArgoCD
argocd login <ARGOCD_SERVER> --username admin --password <initial-password>

# Create a new token
argocd account generate-token --account admin-user
```

---

### 4. Slack Notifications (Optional but Recommended)

To receive deployment notifications in Slack:

#### 4.1 Create Slack Webhook

1. Go to your Slack workspace
2. Create a new app: https://api.slack.com/apps
3. Enable Incoming Webhooks
4. Create a new webhook for your desired channel
5. Copy the webhook URL

#### 4.2 Add Slack Secret to GitHub

```
SLACK_WEBHOOK_URL: <your-slack-webhook-url>
```

---

### 5. Codecov Setup (Optional)

For code coverage reporting:

1. Go to https://codecov.io and sign in with GitHub
2. Enable coverage for your repository
3. No additional GitHub secrets needed (Codecov auto-detects from GitHub)

---

### 6. Kubernetes Cluster Access

Your K8s cluster needs to be:
- Running and accessible
- Have ArgoCD installed and configured
- Have jretirewise namespace created (done by our manifests)

**Verify cluster access:**

```bash
# Test kubectl access
kubectl cluster-info
kubectl get nodes

# Verify jretirewise namespace will be created
kubectl apply -k k8s/base/  # This creates the namespace
```

---

### 7. Domain Configuration (For Production)

The health check and smoke tests expect:
- `https://jretirewise.example.com` to be accessible

**Update this in the workflow:**

Edit `.github/workflows/ci-cd.yml` lines 213, 242, 256, 285:
- Change `jretirewise.example.com` to your actual domain
- Ensure domain has valid TLS certificate (use cert-manager in K8s)

---

## Environment Variables (Already Handled)

The workflow uses these env vars which don't need secrets:

```yaml
REGISTRY: docker.io
IMAGE_NAME: ${{ secrets.DOCKER_USERNAME }}/jretirewise
PYTHON_VERSION: "3.11"
```

These are standard and don't require configuration.

---

## Checklist: Required Setup

### Minimum Setup (To Get Testing + Build Working)

- [ ] Create Docker Hub account
- [ ] Generate Docker Hub access token
- [ ] Add `DOCKER_USERNAME` secret to GitHub
- [ ] Add `DOCKER_PASSWORD` secret to GitHub

**Result**: Tests and builds will run automatically, Docker images will be pushed to Docker Hub

### Full Setup (To Get Deployment Working)

- [ ] Complete Minimum Setup above
- [ ] Install ArgoCD in Kubernetes cluster
- [ ] Get ArgoCD server URL
- [ ] Create ArgoCD application for jretirewise-prod
- [ ] Generate ArgoCD auth token
- [ ] Add `ARGOCD_SERVER` secret to GitHub
- [ ] Add `ARGOCD_AUTH_TOKEN` secret to GitHub
- [ ] Create Kubernetes cluster kubeconfig
- [ ] Update domain in workflow (if not using jretirewise.example.com)
- [ ] Configure TLS certificate for production domain
- [ ] Test ArgoCD sync manually before relying on automation

### Optional Enhancements

- [ ] Create Slack webhook and add `SLACK_WEBHOOK_URL` secret
- [ ] Set up Codecov integration for coverage tracking

---

## Testing Your Setup

### 1. Test Docker Credentials

```bash
# Manually test Docker login
docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
docker pull docker.io/$DOCKER_USERNAME/jretirewise:latest 2>/dev/null || echo "Image doesn't exist yet (expected)"
```

### 2. Test ArgoCD Connection

```bash
# Manually test ArgoCD
argocd login $ARGOCD_SERVER --username admin --password $ARGOCD_AUTH_TOKEN
argocd app list
argocd app get jretirewise-prod
```

### 3. Run Workflow Manually

1. Go to GitHub repository
2. Click "Actions" tab
3. Select "CI/CD Pipeline"
4. Click "Run workflow" → "Run workflow"
5. Watch the workflow execute

---

## Troubleshooting

### Docker Push Fails

**Error**: `denied: requested access to the resource is denied`

**Solution**:
- Verify Docker username is correct
- Verify token (not password) is used
- Check token has read/write permissions
- Token may have expired; generate a new one

### ArgoCD Sync Fails

**Error**: `application not found`

**Solution**:
- Verify application name is `jretirewise-prod` in your cluster
- Verify manifests repository is configured
- Check `k8s/overlays/prod/` path exists in manifests repo

### Health Check Fails

**Error**: `Health check failed after 5 minutes`

**Solution**:
- Verify domain is correct (update in workflow)
- Verify TLS certificate is valid
- Check application is actually deployed
- Verify health endpoint exists at `/health/ready/`

### E2E Tests Timeout

**Error**: `Application not ready yet after multiple attempts`

**Solution**:
- Ensure Playwright tests are properly configured
- Verify test environment has correct database setup
- Check for any missing fixtures or test data setup

---

## GitHub Secrets Summary

| Secret Name | Purpose | Where to Get |
|-----------|---------|-------------|
| `DOCKER_USERNAME` | Docker Hub authentication | Docker Hub account settings |
| `DOCKER_PASSWORD` | Docker Hub authentication | Docker Hub access tokens |
| `ARGOCD_SERVER` | ArgoCD cluster address | From your K8s ArgoCD installation |
| `ARGOCD_AUTH_TOKEN` | ArgoCD authentication | `argocd account generate-token` |
| `SLACK_WEBHOOK_URL` | Slack deployment notifications | Slack API → Incoming Webhooks |

---

## Next Steps

1. **Set up Docker Hub**: Create account and token
2. **Add GitHub secrets**: Configure Docker credentials (minimum)
3. **Create a test push**: Push to `develop` branch to trigger test workflow
4. **Verify test job**: Check GitHub Actions → Test job passes
5. **Verify build job**: Check build creates Docker image on Docker Hub
6. **Set up ArgoCD** (optional): For production deployments
7. **Enable deploy job**: After ArgoCD is configured
8. **Monitor deployments**: Via GitHub Actions and ArgoCD UI

---

## Security Best Practices

1. **Never commit secrets**: Use GitHub Secrets, never hardcode
2. **Rotate tokens regularly**: Regenerate Docker and ArgoCD tokens periodically
3. **Use separate accounts**: Consider separate Docker Hub account for CI/CD
4. **Restrict token scope**: Only grant necessary permissions
5. **Monitor deployments**: Set up Slack notifications to track changes
6. **Audit logs**: Check GitHub Actions logs and ArgoCD audit logs regularly

---

## Questions?

Refer to:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Docker Hub API Documentation](https://docs.docker.com/docker-hub/api/latest/)
- Project [CLAUDE.md](CLAUDE.md) for development guidelines
