Cloudflare Tunnel for Kubernetes Homelab - Working December 2025 Setup
=====================================================================

Tested and verified with Cloudflare Zero Trust (free plan) + Kubernetes + Django apps.

Why this setup works reliably
-----------------------------
- Remote-managed tunnel using token (no config.yaml, no volume bugs)
- All routing rules managed in the Cloudflare dashboard
- Uses short service names only (no .svc.cluster.local DNS issues)
- Free SSL, zero open ports on your firewall

Prerequisites
-------------
- Domain added to Cloudflare (example: jaycurtis.org)
- Zero Trust free plan activated at https://dash.cloudflare.com
- Running Kubernetes cluster

1. Create the Tunnel in Zero Trust Dashboard
--------------------------------------------
1. Go to dash.cloudflare.com → Zero Trust → Access → Tunnels
2. Click "Create a tunnel"
3. Name it anything (e.g. homelab-main)
4. Connector type: Cloudflared
5. Save
6. Copy the long Tunnel token (starts with eyJhIjoi...) - you will need this in k8s

2. Deploy cloudflared in Kubernetes (token mode)
------------------------------------------------
Save this as cloudflared-deployment.yaml:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudflared
  namespace: cloudflared
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloudflared
  template:
    metadata:
      labels:
        app: cloudflared
    spec:
      containers:
      - name: cloudflared
        image: cloudflare/cloudflared:2025.10.1   # stable version, avoids 2025.11.x bugs
        args:
        - tunnel
        - --no-autoupdate
        - --loglevel
        - info
        - run
        - --token
        - "eyJhIjoi...PASTE_YOUR_FULL_TOKEN_HERE..."

Apply it:
kubectl create namespace cloudflared
kubectl apply -f cloudflared-deployment.yaml

3. Add Sites via the Dashboard (repeat for every service)
---------------------------------------------------------
Zero Trust → Tunnels → your tunnel → Public Hostname → Add a public hostname

Example for jRetireWise:
- Subdomain: jretirewise
- Domain: jaycurtis.org
- Type: HTTP
- URL: prod-jretirewise-jretirewise-web-service.jretirewise:80
      (short name only - NO .svc.cluster.local)
- HTTP settings:
      Host header: Host → jretirewise.jaycurtis.org
      No TLS Verify: checked

Save - live in under 30 seconds

4. DNS (once per tunnel)
------------------------
In Cloudflare DNS add a CNAME:
Name:   jretirewise          (or *.jaycurtis.org for wildcard)
Target: <TUNNEL_UUID>.cfargotunnel.com
Proxied: ON (orange cloud)

5. Django / Any App - Critical Fix
----------------------------------
In settings.py (or equivalent):

ALLOWED_HOSTS = [
    'jretirewise.jaycurtis.org',
    'grafana.jaycurtis.org',
    # ...or simply:
    '*',   # safe when behind Cloudflare Tunnel
]

Restart your app deployment after changing.

Adding a New Site (e.g. grafana.jaycurtis.org)
---------------------------------------------
1. Dashboard → Public Hostname → Add another rule
   Subdomain: grafana
   URL: grafana.grafana:3000                 (short name!)
   Host header: grafana.jaycurtis.org
   No TLS Verify: checked
2. Add to ALLOWED_HOSTS if needed
3. Done!

Verification Commands
---------------------
# Watch tunnel logs
kubectl logs -n cloudflared -l app=cloudflared -f

# Test from inside the cluster
kubectl run tmp --rm -i --image=busybox -n cloudflared -- sh
# inside the pod run:
wget -O- --header="Host: jretirewise.jaycurtis.org" http://prod-jretirewise-jretirewise-web-service.jretirewise:80/jRetireWise

You now have secure HTTPS access to everything:
https://jretirewise.jaycurtis.org
https://grafana.jaycurtis.org
https://anything.jaycurtis.org

No ports open. Free forever. Works perfectly in December 2025.

Enjoy your homelab!