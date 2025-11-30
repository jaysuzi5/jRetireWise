# Kubernetes Deployment Guide for jRetireWise

## Overview

This guide provides instructions for deploying jRetireWise to a Kubernetes cluster using Kustomize for configuration management and ArgoCD for GitOps-based deployment.

## Architecture

```
                          ┌─────────────────┐
                          │  Ingress/NGINX  │
                          │   (TLS Term)    │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │                             │
            ┌───────▼────────┐        ┌──────────▼──────┐
            │ jRetireWise Web │        │ jRetireWise Web │
            │  (3-5 replicas) │        │  (3-5 replicas) │
            └────────┬────────┘        └────────┬────────┘
                     │                           │
        ┌────────────┼───────────────────────────┤
        │            │                           │
    ┌───▼──┐    ┌───▼──────┐              ┌─────▼──┐
    │Redis │    │ Postgres │              │ Celery │
    │Cache │    │ Database │              │Worker │
    └──────┘    └──────────┘              └───────┘
```

## Prerequisites

- Kubernetes 1.19+
- kubectl configured with cluster access
- Kustomize 4.0+ (built into kubectl >= 1.14)
- (Optional) ArgoCD for GitOps deployments
- (Optional) cert-manager for SSL/TLS

## Directory Structure

```
k8s/
├── base/                          # Base manifests (environment-agnostic)
│   ├── configmap.yaml             # Configuration values
│   ├── secret.yaml                # Sensitive data (use External Secrets in prod)
│   ├── rbac.yaml                  # ServiceAccount and RBAC rules
│   ├── service.yaml               # Services for all components
│   ├── ingress.yaml               # Ingress configuration
│   ├── deployment-web.yaml        # Django web application
│   ├── deployment-celery.yaml     # Celery worker
│   ├── deployment-redis.yaml      # Redis cache
│   ├── statefulset-postgres.yaml  # PostgreSQL database
│   └── kustomization.yaml         # Base configuration
└── overlays/
    ├── dev/                       # Development environment overrides
    │   ├── kustomization.yaml
    │   ├── deployment-web-patch.yaml
    │   ├── statefulset-postgres-patch.yaml
    │   ├── deployment-redis-patch.yaml
    └── prod/                      # Production environment overrides
        ├── kustomization.yaml
        ├── deployment-web-patch.yaml
        ├── statefulset-postgres-patch.yaml
        ├── deployment-redis-patch.yaml
        └── deployment-celery-patch.yaml
```

## Configuration Management

### ConfigMap

The `configmap.yaml` contains all non-sensitive configuration:

```yaml
DEBUG: "false"
ALLOWED_HOSTS: "jretirewise.example.com,www.jretirewise.example.com"
DATABASE_HOST: "postgres-service"
REDIS_URL: "redis://redis-service:6379/0"
```

**To update ConfigMap:**
```bash
kubectl set env deployment/jretirewise-web DEBUG=true --from=literal=value
```

### Secrets

The `secret.yaml` contains sensitive data:

```yaml
SECRET_KEY: "your-django-secret-key"
DATABASE_PASSWORD: "secure-password"
EMAIL_HOST_PASSWORD: "app-specific-password"
```

**⚠️ IMPORTANT: Secrets Management in Production**

1. **Never commit secrets to Git** - Use External Secrets Operator or Sealed Secrets
2. **Example using External Secrets:**
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: SecretStore
   metadata:
     name: aws-secrets
   spec:
     provider:
       aws:
         auth:
           jwt:
             serviceAccountRef:
               name: jretirewise
         region: us-east-1
   ```

3. **Generate Django SECRET_KEY:**
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

## Deployment Instructions

### Dry Run (View manifests without applying)

```bash
# View base manifests
kubectl kustomize k8s/base

# View development manifests
kubectl kustomize k8s/overlays/dev

# View production manifests
kubectl kustomize k8s/overlays/prod
```

### Development Deployment

```bash
# Create namespace
kubectl create namespace jretirewise-dev

# Apply development configuration
kubectl apply -k k8s/overlays/dev

# Verify deployment
kubectl get deployments -n jretirewise-dev
kubectl get statefulsets -n jretirewise-dev
kubectl get services -n jretirewise-dev
kubectl get ingress -n jretirewise-dev

# Check pod status
kubectl get pods -n jretirewise-dev
kubectl logs -f deployment/dev-jretirewise-web -n jretirewise-dev
```

### Production Deployment

```bash
# Create namespace
kubectl create namespace jretirewise-prod

# Create secrets (BEFORE applying kustomization)
kubectl create secret generic jretirewise-secret \
  --from-literal=SECRET_KEY="your-random-secret-key" \
  --from-literal=DATABASE_PASSWORD="secure-db-password" \
  --from-literal=EMAIL_HOST_PASSWORD="app-password" \
  -n jretirewise-prod

# Apply production configuration
kubectl apply -k k8s/overlays/prod -n jretirewise-prod

# Wait for rollout
kubectl rollout status deployment/prod-jretirewise-web -n jretirewise-prod --timeout=5m
```

## Component Details

### Web Application (Django)

**Deployment**: `deployment-web.yaml`
- **Replicas**: 3 (dev) → 5 (prod)
- **Strategy**: RollingUpdate with no downtime
- **Resources**:
  - Dev: 256Mi RAM, 250m CPU (requests) → 512Mi, 500m (limits)
  - Prod: 512Mi RAM, 500m CPU (requests) → 1Gi, 1000m (limits)

**Health Checks**:
```yaml
startupProbe:      # 30s initial delay, up to 5 minutes to start
readinessProbe:    # Check every 10s, serve traffic after 1 success
livenessProbe:     # Check every 30s, restart on 3 consecutive failures
```

**Init Container**: Runs `python manage.py migrate` before app starts

**Pod Anti-Affinity**: Spreads pods across different nodes for HA

### Database (PostgreSQL)

**StatefulSet**: `statefulset-postgres.yaml`
- **Storage**: 10Gi (dev) → 100Gi (prod)
- **Persistent Volume Claim**: Ensures data survives pod restarts
- **Access**: Service DNS: `postgres-service:5432`

**Backup Strategy** (production):
```bash
# Manual backup
kubectl exec -it postgres-0 -c postgres -- \
  pg_dump -U jretirewise jretirewise | gzip > backup.sql.gz

# Restore from backup
gzip -d backup.sql.gz
kubectl exec -i postgres-0 -c postgres -- \
  psql -U jretirewise jretirewise < backup.sql
```

### Cache Layer (Redis)

**Deployment**: `deployment-redis.yaml`
- **Purpose**: Celery broker, session cache
- **Access**: Service DNS: `redis-service:6379`
- **Persistence**: EmptyDir (acceptable for cache)

### Task Queue (Celery)

**Deployment**: `deployment-celery.yaml`
- **Replicas**: 2 (dev) → 3 (prod)
- **Command**: `celery -A config worker -l info`
- **Concurrency**: 4 worker processes
- **Connection**: Uses Redis broker and PostgreSQL for results

## Network & Security

### Ingress

The Ingress handles:
- **SSL/TLS termination** with cert-manager
- **Domain routing** for jretirewise.example.com
- **Path-based routing** (all paths → web service)

```bash
# Check Ingress status
kubectl get ingress -n jretirewise-prod
kubectl describe ingress jretirewise -n jretirewise-prod

# View TLS certificate
kubectl get certificate -n jretirewise-prod
```

### RBAC

The ServiceAccount `jretirewise` has minimal permissions:
- Read ConfigMaps and Secrets
- Read Pod information
- List Deployments

This follows the principle of least privilege.

### Security Context

All containers run:
- **Non-root user** (uid: 1000)
- **Read-only root filesystem** (where possible)
- **No privilege escalation**
- **Dropped all capabilities**

## Monitoring & Observability

### Logs

```bash
# Tail web application logs
kubectl logs -f deployment/prod-jretirewise-web -n jretirewise-prod --tail=100

# Logs from previous container (if crashed)
kubectl logs deployment/prod-jretirewise-web -n jretirewise-prod --previous

# Stream logs from all web pods
kubectl logs -f deployment/prod-jretirewise-web -n jretirewise-prod -c web --all-containers=true
```

### Metrics

Prometheus annotations are included:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

Add Prometheus scrape config:
```yaml
scrape_configs:
- job_name: 'jretirewise'
  static_configs:
  - targets: ['localhost:8000']
```

### Health Checks

```bash
# Check readiness (can accept traffic)
kubectl exec -it deployment/prod-jretirewise-web -n jretirewise-prod -- \
  curl -s http://localhost:8000/health/ready/ | jq

# Check liveness (still running)
kubectl exec -it deployment/prod-jretirewise-web -n jretirewise-prod -- \
  curl -s http://localhost:8000/health/live/ | jq
```

## Scaling

### Horizontal Scaling (More Pods)

```bash
# Scale web replicas
kubectl scale deployment prod-jretirewise-web --replicas=7 -n jretirewise-prod

# Scale Celery workers
kubectl scale deployment prod-jretirewise-celery --replicas=5 -n jretirewise-prod

# Autoscaling (HPA)
kubectl autoscale deployment prod-jretirewise-web \
  --min=3 --max=10 --cpu-percent=70 -n jretirewise-prod
```

### Vertical Scaling (More Resources)

Edit the patches in `overlays/prod/` and apply:
```bash
kubectl apply -k k8s/overlays/prod -n jretirewise-prod
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n jretirewise-prod

# Check logs for startup errors
kubectl logs <pod-name> -n jretirewise-prod

# Check init container logs
kubectl logs <pod-name> -c migrate -n jretirewise-prod
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:14-alpine --restart=Never -- \
  psql postgresql://jretirewise:password@postgres-service:5432/jretirewise \
  -c "SELECT version();"

# Check Postgres service
kubectl get svc postgres-service -n jretirewise-prod
kubectl nslookup postgres-service.jretirewise-prod
```

### Migration Failures

```bash
# Manually run migrations
kubectl exec -it deployment/prod-jretirewise-web -n jretirewise-prod -- \
  python manage.py migrate

# Check migration status
kubectl exec -it deployment/prod-jretirewise-web -n jretirewise-prod -- \
  python manage.py showmigrations
```

## Backup & Disaster Recovery

### Backup Strategy

```bash
# Backup PostgreSQL
kubectl exec postgres-0 -n jretirewise-prod -- \
  pg_dump -U jretirewise -Fc jretirewise | gzip > jretirewise-backup.sql.gz

# Backup Kubernetes objects
kubectl get all -n jretirewise-prod -o yaml > k8s-backup.yaml

# Backup secrets (store securely!)
kubectl get secret jretirewise-secret -n jretirewise-prod -o yaml > secret-backup.yaml
```

### Recovery

```bash
# Restore PostgreSQL
gzip -d jretirewise-backup.sql.gz
kubectl exec -i postgres-0 -n jretirewise-prod -- \
  pg_restore -U jretirewise -d jretirewise < jretirewise-backup.sql

# Restore Kubernetes objects
kubectl apply -f k8s-backup.yaml
```

## GitOps with ArgoCD

### ArgoCD Application Definition

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jretirewise-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/jretirewise
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: jretirewise-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
  revisionHistoryLimit: 5
```

### Deploy with ArgoCD

```bash
# Create ArgoCD application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: jretirewise-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/jretirewise
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: jretirewise-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# Sync (deploy) the application
argocd app sync jretirewise-prod

# Watch sync progress
argocd app wait jretirewise-prod

# Check application health
argocd app get jretirewise-prod
```

## Performance Tuning

### Database Connection Pooling

Update `configmap.yaml`:
```yaml
DATABASE_CONN_MAX_AGE: "600"  # 10 minute connection pooling
DATABASES_ATOMIC_REQUESTS: "true"
```

### Celery Worker Optimization

In `deployment-celery.yaml`:
```yaml
command:
- celery
- -A
- config
- worker
- -l
- info
- -c  # Worker concurrency
- "8"  # Increase from 4 for more parallelism
- -O
- fair  # Fair scheduling algorithm
```

### Redis Persistence

For production Redis, enable persistence:
```bash
kubectl patch deployment prod-redis -p '{"spec":{"template":{"spec":{"volumes":[{"name":"redis-data","persistentVolumeClaim":{"claimName":"redis-pvc"}}]}}}}'
```

## Cleanup

### Delete Development Environment

```bash
kubectl delete namespace jretirewise-dev
```

### Delete Production Environment

```bash
kubectl delete namespace jretirewise-prod
```

### Delete All Kustomize-managed Resources

```bash
kubectl delete -k k8s/overlays/prod
```

## References

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Kustomize Documentation](https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Django on Kubernetes](https://www.caktusgroup.com/blog/2017/10/18/deploying-django-applications-kubernetes/)
