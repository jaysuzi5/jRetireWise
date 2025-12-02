# GitHub Secrets Required for CI/CD Pipeline

## Quick Setup Checklist

### Step 1: Add Docker Hub Secrets (REQUIRED)

These secrets enable the build job to push Docker images.

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these two secrets:

**Secret 1: DOCKER_USERNAME**
- Value: Your Docker Hub username (e.g., `jaysuzi5`)

**Secret 2: DOCKER_PASSWORD**
- Value: Your Docker Hub personal access token (NOT your password!)
  - Get this from: https://hub.docker.com/settings/security/tokens
  - Create token with read/write permissions
  - Copy the token value

### Step 2: Add ArgoCD Secrets (OPTIONAL - for deployment)

These secrets enable automated deployment to Kubernetes.

**Secret 3: ARGOCD_SERVER**
- Value: Your ArgoCD server URL
  - Examples: `argocd.example.com` or `192.168.1.100:6443`
  - Get this after installing ArgoCD in your K8s cluster

**Secret 4: ARGOCD_AUTH_TOKEN**
- Value: Your ArgoCD authentication token
  - Generate with: `argocd account generate-token --account admin-user`

### Step 3: Add Slack Webhook (OPTIONAL - for notifications)

**Secret 5: SLACK_WEBHOOK_URL**
- Value: Your Slack webhook URL
  - Create at: https://api.slack.com/apps
  - Enable Incoming Webhooks
  - Create webhook for your channel

---

## What Each Secret Does

| Secret | Required? | Purpose |
|--------|-----------|---------|
| DOCKER_USERNAME | ✅ YES | Login to Docker Hub to push images |
| DOCKER_PASSWORD | ✅ YES | Authenticate Docker Hub access |
| ARGOCD_SERVER | ⚠️ OPTIONAL | Connect to your Kubernetes cluster |
| ARGOCD_AUTH_TOKEN | ⚠️ OPTIONAL | Authenticate with ArgoCD for deployments |
| SLACK_WEBHOOK_URL | ❌ NO | Slack deployment notifications (optional) |

---

## Minimum Setup for Initial Testing

To get tests running and images building:

```
DOCKER_USERNAME = <your-docker-hub-username>
DOCKER_PASSWORD = <your-docker-hub-token>
```

That's it! With just these two, the workflow will:
- ✅ Run all tests on every push
- ✅ Build Docker images on successful tests
- ✅ Push images to Docker Hub

---

## Full Setup for Production Deployment

To also enable automatic Kubernetes deployments:

```
DOCKER_USERNAME = <your-docker-hub-username>
DOCKER_PASSWORD = <your-docker-hub-token>
ARGOCD_SERVER = <your-argocd-url>
ARGOCD_AUTH_TOKEN = <your-argocd-token>
SLACK_WEBHOOK_URL = <your-slack-webhook> (optional)
```

With all of these, the workflow will:
- ✅ Run all tests
- ✅ Build Docker images
- ✅ Push to Docker Hub
- ✅ Deploy to Kubernetes via ArgoCD
- ✅ Run E2E tests
- ✅ Notify Slack

---

## How to Get Each Secret

### Docker Hub Credentials

1. Create account at https://hub.docker.com
2. Go to Account Settings → Security → Access Tokens
3. Click "Create Token"
4. Name: `github-actions` (or any name)
5. Permissions: Read, Write, Delete
6. Copy the token
7. Use your username as `DOCKER_USERNAME`
8. Use the token as `DOCKER_PASSWORD`

### ArgoCD Credentials (if deploying)

1. Install ArgoCD in your Kubernetes cluster:
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

2. Get server URL:
   ```bash
   kubectl get svc argocd-server -n argocd
   # Use the external IP or configure port-forward
   ```

3. Get default admin password:
   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

4. Login and create token:
   ```bash
   argocd login <ARGOCD_SERVER> --username admin --password <password>
   argocd account generate-token --account admin-user
   ```

5. Use the token as `ARGOCD_AUTH_TOKEN`

### Slack Webhook (if notifying)

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: `jretirewise`
4. Select your workspace
5. Go to "Incoming Webhooks"
6. Click "Add New Webhook to Workspace"
7. Select your channel
8. Copy the webhook URL
9. Use as `SLACK_WEBHOOK_URL`

---

## Information You Need to Provide

To help you set up, I need to know:

1. **Docker Hub username** - What's your Docker Hub account username?
2. **Is ArgoCD already installed?** - Yes/No
3. **What's your production domain?** - e.g., `jretirewise.example.com`
4. **Do you want Slack notifications?** - Yes/No
5. **ArgoCD server URL** - If using ArgoCD, what's the URL?

---

## How to Add Secrets to GitHub

1. Go to your GitHub repository
2. Click Settings (top right)
3. Left sidebar → "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Name: (use exact names from table above)
6. Value: (paste the secret value)
7. Click "Add secret"
8. Repeat for each secret

---

## Verify Setup Works

After adding secrets, trigger a workflow:

1. Go to repository home
2. Click "Actions" tab
3. Select "CI/CD Pipeline" workflow
4. Click "Run workflow" → "Run workflow"
5. Watch it execute:
   - Tests should pass (green ✓)
   - Build should succeed (image pushed to Docker Hub)
   - Deploy will fail until ArgoCD is configured (expected)

---

## File References

For detailed setup instructions, see:
- `documents/CI_CD_SETUP.md` - Full setup guide
- `.github/workflows/ci-cd.yml` - Workflow definition
- `.github/workflows/test.yml` - Test workflow
- `CLAUDE.md` - Project guidelines

---

## Quick Reference: What Gets Automated

### Trigger: Push to `main` branch
✅ Run tests
✅ Run linting
✅ Build Docker image
✅ Push to Docker Hub
✅ Deploy to Kubernetes (if ArgoCD configured)
✅ Run E2E tests
✅ Notify Slack (if webhook configured)

### Trigger: Push to `develop` branch
✅ Run tests
✅ Run linting
✅ Build Docker image
✅ Push to Docker Hub
❌ Deploy (only on main)
❌ E2E tests (only on main)

### Trigger: Pull Request to `main` or `develop`
✅ Run tests
✅ Run linting
❌ Build (PR code not pushed to main/develop yet)
❌ Deploy (PR code not pushed yet)

---

## Next Steps

1. Decide: Do you want to deploy with ArgoCD or just build images?
2. Get Docker Hub credentials
3. Add GitHub secrets (Docker at minimum)
4. Make a test push to `develop` branch
5. Watch workflow run in Actions tab
6. If deploying: Set up ArgoCD and add those secrets too

Need help? Refer to `documents/CI_CD_SETUP.md` for detailed instructions.
