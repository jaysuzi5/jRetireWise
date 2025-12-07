# OpenTelemetry Fix - Deployment Status

**Date**: December 4, 2025
**Status**: ⏳ Waiting for Docker Image Build to Complete

## Summary

Two critical OpenTelemetry issues have been identified and fixed in the source code:

1. ✅ **Filelog Receiver Container Naming Mismatch** - Fixed
2. ✅ **OTLP Exporter Protocol Mismatch (HTTP vs gRPC)** - Fixed

The fixes are committed to the main branch. The application is now waiting for the Docker image to be built and deployed.

## Issues Fixed

### Issue 1: Filelog Receiver Not Matching Web Container Logs

**Problem**: The OTEL collector's filelog receiver was configured with a wildcard pattern that matched PostgreSQL and Redis sidecars but NOT the main jretirewise web application container.

**Root Cause**: Container naming mismatch
- The pod name contains "jretirewise" (e.g., `prod-jretirewise-jretirewise-web-58cff8585b-hnx5b`)
- The namespace contains "jretirewise"
- But the container name is just `web`
- Kubernetes log filename format: `{pod}_{namespace}_{container}-{id}.log`
- The wildcard pattern `/var/log/containers/*jretirewise*.log` didn't match because the container name component is "web"

**Solution Applied**: Added explicit pattern to `documents/collector-fixed.yaml`:
```yaml
filelog:
  include:
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log  # ← EXPLICIT PATTERN
```

**File Modified**:
- `documents/collector-fixed.yaml` (commit: e31a202)

**Status**: ✅ Ready - User needs to apply this to home-lab repository collector.yaml

---

### Issue 2: OTLP Exporter Using HTTP Instead of gRPC (CRITICAL)

**Problem**: The application was producing repeated `ConnectionResetError: [Errno 104] Connection reset by peer` errors every ~10 seconds when trying to export spans and metrics.

**Root Cause**: Protocol mismatch
- Environment variable configured gRPC endpoint: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-collector.monitoring.svc.cluster.local:4317`
- Port 4317 is the gRPC port (only accepts gRPC protocol)
- Application code was using HTTP OTLP exporters
- Attempted to POST to `http://otel-collector-collector:4317/v1/traces` but port 4317 rejects HTTP requests

**Before (BROKEN)**:
```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

trace_exporter = OTLPSpanExporter(
    endpoint=f"{otel_endpoint}/v1/traces",  # ← HTTP format with /v1/traces path
)

metric_exporter = OTLPMetricExporter(
    endpoint=f"{otel_endpoint}/v1/metrics",  # ← HTTP format with /v1/metrics path
)
```

**After (FIXED)**:
```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

trace_exporter = OTLPSpanExporter(
    endpoint=otel_endpoint,  # ← gRPC endpoint without path suffixes
)

metric_exporter = OTLPMetricExporter(
    endpoint=otel_endpoint,  # ← gRPC endpoint without path suffixes
)
```

**Files Modified**:
- `config/otel.py` (commit: 985afdc "fix: Switch from HTTP to gRPC OTLP exporters to match collector configuration")

**Key Changes**:
- Switched from HTTP to gRPC OTLP exporters
- Removed `/v1/traces` and `/v1/metrics` path suffixes (gRPC doesn't use HTTP REST paths)
- Endpoint is passed directly without modification
- Both trace and metric exporters now use gRPC protocol matching port 4317

**Status**: ✅ Code fixed and committed - Awaiting Docker image build

---

## Current Deployment Status

### Commits Made

| Commit | Message | Status |
|--------|---------|--------|
| e31a202 | fix: Add explicit pattern for jretirewise web container to filelog receiver | ✅ Merged |
| 985afdc | fix: Switch from HTTP to gRPC OTLP exporters to match collector configuration | ✅ Merged |

### GitHub Actions Pipeline

- **Run ID**: 19946162458
- **Triggered**: ~5 minutes ago via push to main
- **Current Stage**: Tests (in progress)
- **Next Stage**: Build Docker image (will run after tests pass)

### Application Status

**Current Pods** (with OLD image from ~5.5 hours ago):
- `prod-jretirewise-jretirewise-web-58cff8585b-cf947` (created 22:36:01 UTC)
- `prod-jretirewise-jretirewise-web-58cff8585b-stxsw` (created 22:36:01 UTC)

**Current Behavior**:
- Pods are running but still have HTTP exporter errors (old image)
- Producing: `ConnectionResetError: [Errno 104] Connection reset by peer`
- Repeating every ~10 seconds as span export batches fail
- No traces/metrics successfully exported to OTEL collector

**Expected After Deployment**:
- New pods will have gRPC exporters
- No more connection reset errors
- Traces/metrics will successfully export to OTEL collector
- Container logs will be captured by filelog receiver (once home-lab collector.yaml is updated)

---

## Next Steps

### 1. Wait for Docker Image Build (GitHub Actions)

The CI/CD pipeline is currently building. Monitor with:

```bash
gh run view 19946162458 -R jaysuzi5/jRetireWise
```

Expected timeline:
- Tests: ~2-3 minutes (currently running)
- Docker Build: ~5-10 minutes
- Image Push to Docker Hub: ~2-5 minutes
- **Total**: ~10-20 minutes

### 2. Verify Deployment

Once the image is built and pushed, Kubernetes will automatically pull the new image (due to `:latest` tag) during the next pod restart.

To force immediate update:
```bash
kubectl delete pods -n jretirewise -l app=jretirewise,component=web --grace-period=30
kubectl wait --for=condition=ready pod -l app=jretirewise,component=web -n jretirewise --timeout=90s
```

### 3. Verify Logs Show No Connection Errors

```bash
kubectl logs -n jretirewise prod-jretirewise-jretirewise-web-* --tail=50 2>&1 | grep -i "connection\|error"
```

**Expected**: No `ConnectionResetError` messages (or much fewer)

### 4. Verify Traces in OTEL Collector

```bash
kubectl logs -n monitoring otel-collector-collector-* --tail=50 2>&1 | grep -i "jretirewise\|trace"
```

**Expected**: Should see trace data being received from jretirewise spans

### 5. Apply Filelog Receiver Fix to Home-Lab Repository

The user needs to update their home-lab repository's OTEL collector configuration to include the filelog receiver fix. See: `documents/OTEL_COLLECTOR_UPGRADE_GUIDE.md` and `documents/collector-fixed.yaml` for reference.

Key change:
```yaml
filelog:
  include:
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log  # ← ADD THIS LINE
```

---

## Documentation Reference

- **Root Cause Analysis**: `documents/FILELOG_FIX_ROOT_CAUSE.md` - Explains the container naming issue
- **OTEL Collector Upgrade**: `documents/OTEL_COLLECTOR_UPGRADE_GUIDE.md` - Complete guide for updating collector configuration
- **Troubleshooting Summary**: `documents/OTEL_TROUBLESHOOTING_SUMMARY.md` - Comprehensive summary of both issues and fixes
- **Fixed Collector YAML**: `documents/collector-fixed.yaml` - Complete corrected collector configuration

---

## Timeline

| Time | Event |
|------|-------|
| ~5min ago | Commit 985afdc pushed (gRPC exporter fix) |
| Now | GitHub Actions tests running |
| +2-3min | Tests complete |
| +7-13min | Docker image built and pushed |
| +20-25min | New image deployed to Kubernetes |
| +25-30min | Connection errors should disappear |
| +30-35min | Traces should appear in OTEL collector |

---

## Key Technical Details

### OTLP Protocol Differences

| Aspect | gRPC | HTTP |
|--------|------|------|
| Port | 4317 | 4318 |
| Protocol | Binary (HTTP/2) | JSON (HTTP/1.1) |
| Import | `otlp.proto.grpc` | `otlp.proto.http` |
| Endpoint Path | None (direct) | `/v1/traces`, `/v1/metrics` |
| Overhead | Low | Moderate |

**Critical Rule**: Match the protocol to the endpoint port. Port 4317 = gRPC, Port 4318 = HTTP.

### Kubernetes Container Log Naming

```
{pod-name}_{namespace}_{container-name}-{container-id}.log
```

Example:
```
prod-jretirewise-jretirewise-web-58cff8585b-hnx5b_jretirewise_web-abc123def456.log
                                              ^^^^^^^^^^^   ^^^
                                              namespace   container-name (NOT pod name)
```

The container name is the critical component that wildcard patterns must match.

---

## How to Monitor Progress

### Check GitHub Actions Build
```bash
gh run list -R jaysuzi5/jRetireWise --limit 1
gh run view 19946162458 -R jaysuzi5/jRetireWise
```

### Check if New Image is Deployed
```bash
kubectl get pods -n jretirewise -l app=jretirewise,component=web \
  -o jsonpath='{range .items[*]}{.metadata.creationTimestamp} {.spec.containers[0].image}{"\n"}{end}'
```

If creation timestamp is more recent than 22:36:01 UTC, new image is deployed.

### Check for Connection Errors
```bash
kubectl logs -n jretirewise -l app=jretirewise,component=web --tail=100 2>&1 | grep -i "connection"
```

Old image will show errors. New image should show none.

### Check OTEL Collector Receives Traces
```bash
kubectl logs -n monitoring otel-collector-collector-* --tail=100 2>&1 | grep "jretirewise"
```

Should see trace/metric records from jretirewise application.

---

**Status**: All code fixes committed. Awaiting automated Docker build and deployment. User action required after deployment: Update home-lab OTEL collector configuration with filelog receiver pattern.
