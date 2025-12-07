# Root Cause Analysis: jretirewise Logs Not Appearing in OTEL Collector

## Problem Summary

The OTEL collector filelog receiver was configured and running successfully, but it was NOT capturing logs from the jretirewise web application pods. The collector was matching files for emporia, todo, postgres, and redis sidecars, but completely missing the main application container.

## Root Cause

**Container Naming Mismatch**: The jretirewise web pods have a container named `web` (not `jretirewise`), which prevented the wildcard pattern from matching.

### What Was Happening

**Glob Pattern Used**:
```
/var/log/containers/*jretirewise*.log
```

**Files That WERE Matched**:
- `/var/log/containers/prod-jretirewise-postgres-0_jretirewise_postgres-*.log` ✅ (has "jretirewise" in name)
- `/var/log/containers/prod-jretirewise-redis-5c4d9446ff-vx9sr_jretirewise_redis-*.log` ✅ (has "jretirewise" in name)

**Files That Were NOT Matched**:
- `/var/log/containers/prod-jretirewise-jretirewise-web-58cff8585b-hnx5b_jretirewise_web-*.log` ❌ (container name is `web`, not `jretirewise`)

### The Container Naming Structure

Kubernetes container log filenames follow this structure:
```
{pod-name}_{namespace}_{container-name}-{container-id}.log
```

For jretirewise:
- Pod name: `prod-jretirewise-jretirewise-web-58cff8585b-hnx5b`
- Namespace: `jretirewise`
- **Container name: `web`** ← This is the critical part
- Container ID: hash

So the actual filename is:
```
prod-jretirewise-jretirewise-web-58cff8585b-hnx5b_jretirewise_web-[container-id].log
```

The pattern `/var/log/containers/*jretirewise*.log` does NOT match because while the pod name and namespace have "jretirewise", the **container name is just "web"**.

## Solution

Add an explicit pattern for the web container:

```yaml
filelog:
  include:
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log  # ← EXPLICIT PATTERN
    - /var/log/containers/*todo*.log
    - /var/log/containers/*emporia*.log
```

### Why This Works

The explicit pattern `/var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log` directly matches the container log filename structure:
- `prod-jretirewise-jretirewise-web` = pod name
- `_jretirewise_` = separator and namespace
- `web-` = container name
- `*.log` = matches any container ID

## Implementation

### Step 1: Update Your OTEL Collector Configuration

In your home-lab repository at `cluster/infrastructure/monitoring/opentelementry-collector/collector.yaml`, update the filelog receiver `include` paths:

```yaml
receivers:
  filelog:
    include:
      - /var/log/containers/*jretirewise*.log
      - /var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log
      - /var/log/containers/*todo*.log
      - /var/log/containers/*emporia*.log
```

Or alternatively, use the corrected `collector-fixed.yaml` from the jRetireWise repository as a reference.

### Step 2: Apply the Configuration

GitOps will automatically apply the changes, or manually restart the OTEL collector:

```bash
kubectl rollout restart deployment/otel-collector-collector -n monitoring
```

### Step 3: Verify

Check that the filelog receiver now matches the web container logs:

```bash
kubectl logs -n monitoring otel-collector-collector-* --tail=50 | grep "prod-jretirewise-jretirewise-web"
```

You should see output like:
```
"paths": [..., "/var/log/containers/prod-jretirewise-jretirewise-web-58cff8585b-hnx5b_jretirewise_web-abc123def456.log", ...]
```

### Step 4: Verify Logs in Splunk

Generate some traffic to the jretirewise application:

```bash
curl http://192.168.86.229/jretirewise/
```

Then search in Splunk:

```
index="otel_logging" sourcetype="otel:logs" jretirewise
```

You should now see application logs with full trace context fields.

## Key Learning

When using Kubernetes container log patterns:
1. **Container name matters** - The container name (3rd component) must match, not just the pod or namespace
2. **Use explicit patterns when wildcards fail** - If a wildcard pattern isn't matching, fall back to explicit patterns that directly target the container you need
3. **Understand the naming structure** - Kubernetes uses: `{pod}_{namespace}_{container}-{id}.log`

## References

- Updated documentation: `documents/OTEL_COLLECTOR_UPGRADE_GUIDE.md`
- Fixed YAML configuration: `documents/collector-fixed.yaml`
- OTEL Filelog Receiver: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/filelogreceiver
