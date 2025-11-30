# ArgoCD Local Setup with Cloudflare Tunnel

This guide covers setting up GitHub Actions to deploy to a locally-running ArgoCD instance using Cloudflare Tunnel for secure public access.

## Prerequisites

- ArgoCD is already installed and running on your local Kubernetes cluster
- ArgoCD is accessible at `192.168.86.229` (your local network IP)
- You have a GitHub repository with the jRetireWise CI/CD workflow
- You have Docker Hub credentials configured in GitHub Secrets

## Overview

Since ArgoCD is only accessible on your local network (`192.168.86.229`), GitHub Actions runners (which run in the cloud) cannot directly reach it. Cloudflare Tunnel solves this by:

1. Creating a secure tunnel from your local ArgoCD to Cloudflare's network
2. Exposing it publicly via a Cloudflare domain (e.g., `https://jretirewise-argocd.your-domain.com`)
3. GitHub Actions connects to the public Cloudflare URL
4. Traffic is encrypted end-to-end

**Key benefit:** Your ArgoCD stays on your local network without public exposure. Only the tunnel connection is publicly accessible.

---

## Step 1: Install Cloudflare Wrangler

Cloudflare Wrangler is the CLI tool for managing tunnels.

### macOS
```bash
brew install cloudflare-wrangler
```

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.wrangler.dev | bash
```

### Windows
Download from: https://github.com/cloudflare/wrangler/releases

### Verify Installation
```bash
wrangler --version
```

---

## Step 2: Set Up Cloudflare Account

1. Go to https://www.cloudflare.com
2. Create a free account (or use existing account)
3. Add your domain (or use Cloudflare's free domain)
4. Note your Cloudflare Account ID (found in Settings)

---

## Step 3: Authenticate Wrangler

Authenticate Wrangler with your Cloudflare account:

```bash
wrangler login
```

This will:
1. Open a browser to Cloudflare's authorization page
2. Ask for permission to manage your account
3. Create an API token automatically
4. Save credentials locally

**Verify authentication:**
```bash
wrangler whoami
```

---

## Step 4: Create the Tunnel

Create a tunnel named `jretirewise-argocd`:

```bash
wrangler tunnel create jretirewise-argocd
```

Output will show:
```
Tunnel credentials have been saved to /Users/username/.wrangler/state/certs/xxx.json
Tunnel ID: abc123def456
Tunnel name: jretirewise-argocd
```

**Save the Tunnel ID** - you'll need it if you need to delete the tunnel later.

---

## Step 5: Verify ArgoCD is Running

Before creating the public route, verify ArgoCD is accessible locally:

```bash
# Check if ArgoCD API is accessible
curl -k https://192.168.86.229/api/version || curl http://192.168.86.229/api/version

# Or check the service
kubectl get svc argocd-server -n argocd
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Then visit http://localhost:8080
```

Note the port number (usually 443 or 8080). Use this in the next step.

---

## Step 6: Create Public Route (Optional - for DNS record)

This step is optional if you just want to use the Cloudflare tunnel domain directly.

If you want a custom domain, create a CNAME record:

1. Go to your Cloudflare dashboard
2. Select your domain
3. Go to DNS records
4. Add a CNAME record:
   - Name: `jretirewise-argocd`
   - Value: `jretirewise-argocd.cfargotunnel.com`
   - Proxy status: Proxied

Or use wrangler:
```bash
wrangler tunnel route dns jretirewise-argocd your-domain.com
```

**Note:** If you don't have a custom domain, Cloudflare will generate a public URL like `jretirewise-argocd-xxxx.cfargotunnel.com`

---

## Step 7: Start the Tunnel

Keep this tunnel running while GitHub Actions jobs execute. You have two options:

### Option A: Manual Tunnel (Development/Testing)

```bash
# Replace 443 with the correct ArgoCD port if different
wrangler tunnel run --url http://192.168.86.229:443 jretirewise-argocd
```

Output will show:
```
Your tunnel is ready to accept traffic and route it to http://192.168.86.229:443
```

**Keep this terminal running.** The tunnel will stay active as long as this command is running.

### Option B: Background Tunnel (Recommended for Production)

Run the tunnel in the background:

```bash
# Start tunnel in background
nohup wrangler tunnel run --url http://192.168.86.229:443 jretirewise-argocd > argocd-tunnel.log 2>&1 &

# Verify it's running
ps aux | grep wrangler

# View logs
tail -f argocd-tunnel.log
```

Or use a process manager like `systemd` (Linux) or `launchd` (macOS).

---

## Step 8: Get Your Public URL

Once the tunnel is running, you have a few ways to access it:

### Using Custom Domain (if you created route in Step 6)
```
https://jretirewise-argocd.your-domain.com
```

### Using Default Cloudflare URL
The tunnel will generate a default URL like:
```
https://jretirewise-argocd-xxxx.cfargotunnel.com
```

To find this URL:
```bash
wrangler tunnel info jretirewise-argocd
```

---

## Step 9: Test the Tunnel Connection

Verify the tunnel is working:

```bash
# Replace with your actual URL
curl https://jretirewise-argocd.your-domain.com/api/version

# If using default Cloudflare URL
curl https://jretirewise-argocd-xxxx.cfargotunnel.com/api/version
```

Expected response: ArgoCD API version information

---

## Step 10: Configure GitHub Secrets

Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Secret 1: ARGOCD_SERVER
```
Value: https://jretirewise-argocd.your-domain.com
```
Or if using default Cloudflare URL:
```
Value: https://jretirewise-argocd-xxxx.cfargotunnel.com
```

### Secret 2: ARGOCD_AUTH_TOKEN
This should already be configured from earlier setup. If not:

```bash
# Get from your ArgoCD instance
argocd account generate-token --account admin-user
```

Then add to GitHub Secrets with the token value.

---

## Step 11: Verify Workflow Configuration

The workflow file `.github/workflows/ci-cd.yml` should have:

```yaml
deploy:
  runs-on: ubuntu-latest
  name: Deploy to Kubernetes
  needs: build
  if: github.ref == 'refs/heads/main'

  steps:
    - name: Set up ArgoCD CLI
      run: |
        curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/download/v2.8.0/argocd-linux-amd64
        chmod +x /usr/local/bin/argocd

    - name: Configure ArgoCD
      env:
        ARGOCD_SERVER: ${{ secrets.ARGOCD_SERVER }}
        ARGOCD_AUTH_TOKEN: ${{ secrets.ARGOCD_AUTH_TOKEN }}
      run: |
        argocd login $ARGOCD_SERVER --insecure --username admin --password $ARGOCD_AUTH_TOKEN

    - name: Sync ArgoCD application
      env:
        ARGOCD_SERVER: ${{ secrets.ARGOCD_SERVER }}
        ARGOCD_AUTH_TOKEN: ${{ secrets.ARGOCD_AUTH_TOKEN }}
      run: |
        argocd app sync jretirewise-prod --force
        argocd app wait jretirewise-prod --sync --timeout 300
```

The `--insecure` flag allows the workflow to accept the tunnel's certificate without validation (acceptable for local development).

---

## Step 12: Create ArgoCD Application

If you haven't already, create an ArgoCD Application for jRetireWise:

```bash
# Login to ArgoCD
argocd login 192.168.86.229 --username admin

# Create application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jretirewise-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jaysuzi5/jRetireWise
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
EOF
```

Verify the application was created:
```bash
argocd app list
argocd app get jretirewise-prod
```

---

## Step 13: Test the Complete Setup

### Manual Test

```bash
# Get your tunnel URL
ARGOCD_SERVER="https://jretirewise-argocd.your-domain.com"
ARGOCD_TOKEN="your-auth-token"

# Login
argocd login $ARGOCD_SERVER --insecure --username admin --password $ARGOCD_TOKEN

# List applications
argocd app list

# Test sync
argocd app sync jretirewise-prod --force
```

### Workflow Test

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "CI/CD Pipeline" workflow
4. Click "Run workflow" → Run workflow
5. Watch the deployment job:
   - Should connect to ArgoCD via tunnel
   - Should sync the application
   - Should pass health checks
   - Should complete successfully

---

## Troubleshooting

### Tunnel Connection Fails

**Error:** `Failed to connect to tunnel`

**Solution:**
```bash
# Check tunnel status
wrangler tunnel list

# Restart tunnel
wrangler tunnel run --url http://192.168.86.229:443 jretirewise-argocd
```

### ArgoCD Login Fails

**Error:** `authentication failed: login unsuccessful`

**Cause:** Token may be invalid or expired

**Solution:**
```bash
# Generate new token
argocd account generate-token --account admin-user

# Update GitHub secret with new token
```

### Health Check Fails

**Error:** `Health check failed after 5 minutes`

**Cause:** Application not deployed or health endpoint failing

**Solution:**
```bash
# Check application status
argocd app get jretirewise-prod
argocd app sync jretirewise-prod

# Check pod status
kubectl get pods -n jretirewise
kubectl logs -n jretirewise <pod-name>
```

### SSL Certificate Verification Error

**Error:** `certificate verify failed`

**Note:** The workflow uses `--insecure` flag, so this shouldn't occur. If it does:

Verify the flag is present in workflow:
```yaml
argocd login $ARGOCD_SERVER --insecure --username admin --password $ARGOCD_AUTH_TOKEN
```

### Tunnel Keeps Disconnecting

**Cause:** Process killed or network issue

**Solution:** Use a process manager or systemd service to keep tunnel running

**Example systemd service (Linux):**
```ini
# /etc/systemd/system/argocd-tunnel.service
[Unit]
Description=ArgoCD Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=youruser
ExecStart=/usr/local/bin/wrangler tunnel run --url http://192.168.86.229:443 jretirewise-argocd
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable argocd-tunnel
sudo systemctl start argocd-tunnel
sudo systemctl status argocd-tunnel
```

---

## Important Notes

### Certificate Security

- The Cloudflare Tunnel uses Cloudflare's certificate for the public HTTPS connection
- Your local ArgoCD connection (192.168.86.229) remains on HTTP
- The tunnel encrypts traffic end-to-end between GitHub Actions and Cloudflare
- Using `--insecure` in the workflow is safe because you're trusting Cloudflare's certificate

### Tunnel Availability

- **Keep the tunnel running** whenever you want GitHub Actions to deploy
- If the tunnel stops, deployments will fail
- Use a process manager or systemd service for production reliability
- Consider systemd service or Docker container to keep it running

### ArgoCD Application

- Make sure the ArgoCD Application `jretirewise-prod` exists in your cluster
- Application should point to your jRetireWise repository and `k8s/overlays/prod` path
- Verify application can sync manually before relying on automation

### Network Considerations

- Local IP `192.168.86.229` should remain consistent (set static IP or DHCP reservation)
- If IP changes, update the tunnel command to point to new IP
- Keep tunnel running on reliable machine/network

---

## Maintenance

### Checking Tunnel Status

```bash
# List tunnels
wrangler tunnel list

# Get tunnel info
wrangler tunnel info jretirewise-argocd

# View tunnel logs
tail -f argocd-tunnel.log
```

### Updating ArgoCD

When you update ArgoCD version:
1. Stop the tunnel
2. Update ArgoCD in Kubernetes
3. Verify ArgoCD is accessible at 192.168.86.229
4. Restart the tunnel

### Rotating Auth Tokens

Periodically rotate your ArgoCD auth token:

```bash
# Generate new token
argocd account generate-token --account admin-user

# Update GitHub secret with new token
# (Go to GitHub Settings → Secrets → Edit ARGOCD_AUTH_TOKEN)
```

---

## Reference

### Key Files and Locations

- Tunnel config: `~/.wrangler/state/certs/`
- Workflow file: `.github/workflows/ci-cd.yml`
- ArgoCD connection: GitHub Secrets (ARGOCD_SERVER, ARGOCD_AUTH_TOKEN)
- Application manifest: `k8s/overlays/prod/`

### Useful Commands

```bash
# Start tunnel
wrangler tunnel run --url http://192.168.86.229:443 jretirewise-argocd

# Test tunnel
curl https://jretirewise-argocd.your-domain.com/api/version

# Login to ArgoCD via tunnel
argocd login https://jretirewise-argocd.your-domain.com --insecure

# Sync application
argocd app sync jretirewise-prod --force

# Watch deployment
kubectl get pods -n jretirewise -w
```

### Documentation Links

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Wrangler CLI Reference](https://developers.cloudflare.com/workers/wrangler/cli-wrangler/)
- [ArgoCD CLI Reference](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd/)
- [jRetireWise CI/CD Setup](./CI_CD_SETUP.md)

---

## Summary

1. ✅ Install Wrangler
2. ✅ Authenticate with Cloudflare
3. ✅ Create tunnel named `jretirewise-argocd`
4. ✅ Start tunnel pointing to `http://192.168.86.229:443`
5. ✅ Get public URL from tunnel
6. ✅ Add `ARGOCD_SERVER` to GitHub Secrets
7. ✅ Verify `ARGOCD_AUTH_TOKEN` in GitHub Secrets
8. ✅ Create ArgoCD Application `jretirewise-prod`
9. ✅ Test manually via CLI
10. ✅ Test via GitHub Actions workflow
11. ✅ Keep tunnel running for deployments

You're now ready to deploy to your local Kubernetes cluster from GitHub Actions!
