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

## Step 1: Install Cloudflared

Cloudflared is the CLI tool for managing Cloudflare Tunnels.

**Note:** Do not use `wrangler` (that's for Cloudflare Workers). We need `cloudflared` instead.

### macOS
```bash
brew install cloudflare/cloudflare/cloudflared
```

### Linux (Ubuntu/Debian)
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

### Windows
Download from: https://github.com/cloudflare/cloudflared/releases

### Verify Installation
```bash
cloudflared --version
```

Expected output: `cloudflared version 2025.x.x`

---

## Step 2: Set Up Cloudflare Account

1. Go to https://www.cloudflare.com
2. Create a free account (or use existing account)
3. Add your domain (or use Cloudflare's free domain)
4. Note your Cloudflare Account ID (found in Settings)

---

## Step 3: Authenticate Cloudflared

Authenticate Cloudflared with your Cloudflare account:

```bash
cloudflared tunnel login
```

This will:
1. Open a browser to Cloudflare's authorization page
2. Ask permission to create tunnels
3. Generate a certificate automatically
4. Save credentials locally to `~/.cloudflared/cert.pem`

**Verify authentication:**
```bash
cloudflared tunnel list
```

If successful, you'll see any existing tunnels (likely empty on first run).

---

## Step 4: Create the Tunnel

Create a tunnel named `jretirewise-argocd`:

```bash
cloudflared tunnel create jretirewise-argocd
```

Output will show:
```
Tunnel credentials have been saved to /Users/username/.cloudflared/abc123def456.json
Tunnel ID: abc123def456
Tunnel Name: jretirewise-argocd
```

**Save the Tunnel ID** - you'll need it if you need to delete the tunnel later.

**Verify tunnel was created:**
```bash
cloudflared tunnel list
```

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

## Step 6: Create Public Route (Optional - for Custom Domain)

This step is optional. You have two options:

### Option A: Use Default Cloudflare Tunnel URL (Easiest)

Cloudflare automatically generates a public URL. Skip this step and go to Step 7.

### Option B: Create Route with Custom Domain

If you want a custom domain like `jretirewise-argocd.your-domain.com`:

```bash
cloudflared tunnel route dns jretirewise-argocd your-domain.com
```

This will:
1. Create a CNAME record in your Cloudflare DNS
2. Point it to the Cloudflare tunnel infrastructure
3. Give you a URL like `https://jretirewise-argocd.your-domain.com`

**Note:** You must own the domain and have it set up in Cloudflare for this to work.

To use the auto-generated URL instead, just skip this step.

---

## Step 7: Start the Tunnel

Keep this tunnel running while GitHub Actions jobs execute. You have two options:

### Option A: Manual Tunnel (Development/Testing)

```bash
# Replace 443 with the correct ArgoCD port if different
cloudflared tunnel run jretirewise-argocd --url http://192.168.86.229:443
```

Output will show:
```
INF Connection registered
INF Registered tunnel connection connIndex=0
INF Tunnel running at https://jretirewise-argocd.cfargotunnel.com
INF Proxying traffic from tunnel to http://192.168.86.229:443
```

**Keep this terminal running.** The tunnel will stay active as long as this command is running.

To stop the tunnel, press `Ctrl+C`.

### Option B: Background Tunnel (Recommended for Production)

Run the tunnel in the background:

```bash
# Start tunnel in background
nohup cloudflared tunnel run jretirewise-argocd --url http://192.168.86.229:443 > argocd-tunnel.log 2>&1 &

# Verify it's running
ps aux | grep cloudflared

# View logs
tail -f argocd-tunnel.log
```

Or use a process manager like `systemd` (Linux) or `launchd` (macOS) - see Troubleshooting section for systemd example.

---

## Step 8: Get Your Public URL

Once the tunnel is running, you have two options:

### Using Default Cloudflare URL (Easiest)

The tunnel generates a default URL automatically. You saw it in Step 7 output:
```
https://jretirewise-argocd.cfargotunnel.com
```

Or get it anytime with:
```bash
cloudflared tunnel info jretirewise-argocd
```

### Using Custom Domain (if you created route in Step 6)
```
https://jretirewise-argocd.your-domain.com
```

**Note:** The custom domain option requires owning a domain and setting it up in Cloudflare. For quick setup, just use the default Cloudflare URL.

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

**Error:** `Failed to connect to tunnel` or tunnel appears inactive

**Solution:**
```bash
# Check tunnel status
cloudflared tunnel list

# Check tunnel info
cloudflared tunnel info jretirewise-argocd

# Restart tunnel (stop and start again)
# First, kill the running process: Ctrl+C or pkill cloudflared
cloudflared tunnel run jretirewise-argocd --url http://192.168.86.229:443
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
cloudflared tunnel list

# Get tunnel info and public URL
cloudflared tunnel info jretirewise-argocd

# View tunnel logs (if running in background)
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
cloudflared tunnel run jretirewise-argocd --url http://192.168.86.229:443

# Get tunnel public URL
cloudflared tunnel info jretirewise-argocd

# Test tunnel connection
curl https://jretirewise-argocd.cfargotunnel.com/api/version

# Login to ArgoCD via tunnel URL
# Replace with your actual tunnel URL from cloudflared tunnel info
argocd login https://jretirewise-argocd.cfargotunnel.com --insecure

# Sync application
argocd app sync jretirewise-prod --force

# Watch deployment
kubectl get pods -n jretirewise -w
```

### Documentation Links

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflared CLI Reference](https://github.com/cloudflare/cloudflared)
- [ArgoCD CLI Reference](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd/)
- [jRetireWise CI/CD Setup](./CI_CD_SETUP.md)

---

## Summary

1. ✅ Install Cloudflared: `brew install cloudflare/cloudflare/cloudflared`
2. ✅ Authenticate: `cloudflared tunnel login`
3. ✅ Create tunnel: `cloudflared tunnel create jretirewise-argocd`
4. ✅ Start tunnel: `cloudflared tunnel run jretirewise-argocd --url http://192.168.86.229:443`
5. ✅ Get public URL: `cloudflared tunnel info jretirewise-argocd`
6. ✅ Add `ARGOCD_SERVER` to GitHub Secrets with your tunnel URL
7. ✅ Verify `ARGOCD_AUTH_TOKEN` in GitHub Secrets
8. ✅ Create ArgoCD Application `jretirewise-prod` (in your K8s cluster)
9. ✅ Test tunnel connection: `curl https://jretirewise-argocd.cfargotunnel.com/api/version`
10. ✅ Test via GitHub Actions workflow
11. ✅ Keep tunnel running for deployments

You're now ready to deploy to your local Kubernetes cluster from GitHub Actions!

**Remember:** Keep the tunnel running whenever you want deployments to work. Use `cloudflared tunnel run ...` in a persistent terminal or background process.
