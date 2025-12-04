# OTEL Collector Upgrade Guide - Filelog Receiver Integration

## Overview

This guide provides the corrected OpenTelemetry Collector configuration with the filelog receiver for collecting jretirewise pod logs.

## What Was Wrong

Your current configuration had two critical issues:

### Issue 1: Incorrect Filelog Configuration (Legacy Syntax)
```yaml
# WRONG - Old/incorrect syntax
filelog:
  include_paths:
    - /var/log/containers/*jretirewise*.log
  exclude_paths:
    - /var/log/containers/*_kube-system_*.log
  multiline_parser:
    type: json
    parse_from: body
```

The older OTEL Collector versions used different field names. The current contrib version requires:
- `include` instead of `include_paths`
- `exclude` instead of `exclude_paths`
- `multiline_type` and `multiline_line_start_pattern` instead of `multiline_parser`

### Issue 2: Wrong Processor Name
```yaml
# WRONG - underscore in name
resource_detection:
  detectors:
    - kubernetes
```

The correct processor name is `resourcedetection` (no underscore, one word).

### Issue 3: Invalid Telemetry Configuration
```yaml
# WRONG - metrics.address syntax
service:
  telemetry:
    metrics:
      level: detailed
      address: "0.0.0.0:8889"
```

Remove the invalid telemetry.metrics section - it causes configuration validation errors.

## Key Changes Made

### 1. Image Updated
```yaml
# OLD
image: otel/opentelemetry-collector-contrib:0.96.0

# NEW
image: otel/opentelemetry-collector-contrib:latest
```

Upgraded to `latest` to ensure filelog receiver is available. You can also use a specific version like `0.97.0` or higher.

### 2. Filelog Receiver Fixed (Latest Syntax)
```yaml
# NOW CORRECT - Updated syntax for latest contrib version
filelog:
  include_paths:
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/*todo*.log
    - /var/log/containers/*emporia*.log
  exclude_paths:
    - /var/log/containers/*_kube-system_*.log
    - /var/log/containers/*_kube-public_*.log
    - /var/log/containers/*_kube-node-lease_*.log
  multiline_type: json
  multiline_line_start_pattern: '^\{'
```

Key updates:
- `multiline_type: json` replaces the old `multiline_parser.type` field
- `multiline_line_start_pattern: '^\{'` detects JSON log lines (starts with `{` character)

### 3. Processor Name Fixed
```yaml
# NOW CORRECT - one word, no underscore
resourcedetection:
  detectors:
    - kubernetes
    - env
  override: false
  timeout: 5s
```

### 4. Logs Pipeline Updated
```yaml
# NOW INCLUDES resourcedetection processor
logs:
  receivers: [otlp, filelog]
  processors: [batch, attributes, resourcedetection]
  exporters: [splunk_hec, debug]
```

## Deployment Instructions

### Step 1: Update Your Collector Configuration

In your home-lab repository, replace the collector.yaml file content with the corrected YAML from `collector-fixed.yaml` provided in this directory.

Key command:
```bash
cp collector-fixed.yaml <your-home-lab-repo>/cluster/infrastructure/monitoring/opentelementry-collector/collector.yaml
```

Or manually update these sections:
- Update image to `otel/opentelemetry-collector-contrib:latest`
- Fix filelog receiver (remove resource_detection from it)
- Fix processor name to `resourcedetection`
- Update logs pipeline to include `resourcedetection` processor

### Step 2: Commit and Push

```bash
cd <your-home-lab-repo>
git add cluster/infrastructure/monitoring/opentelementry-collector/collector.yaml
git commit -m "fix: Update OTEL Collector with corrected filelog receiver and processor names"
git push origin main
```

### Step 3: Verify the Deployment

The collector should apply automatically via GitOps. Verify with:

```bash
# Check pod is running
kubectl get pods -n monitoring -l app.kubernetes.io/name=otel-collector

# Check logs for successful startup
kubectl logs -n monitoring -l app.kubernetes.io/name=otel-collector | grep -i "filelog\|processor\|error" | head -20
```

### Step 4: Generate Test Logs

Trigger some requests to jretirewise to generate logs:

```bash
curl -s http://192.168.86.229/jretirewise/ > /dev/null
curl -s http://192.168.86.229/jretirewise/api/users > /dev/null
```

### Step 5: Verify Logs in OTEL Collector

Check that filelog receiver is reading logs:

```bash
kubectl logs -n monitoring -l app.kubernetes.io/name=otel-collector -f | grep -i "jretirewise\|filelog"
```

You should see log entries being processed.

### Step 6: Verify Logs in Splunk

Search in Splunk:
```
source="otel" service="jretirewise"
```

Or broader search:
```
sourcetype="otel:logs" jretirewise
```

You should see JSON logs with trace context fields:
- `otelTraceID`
- `otelSpanID`
- `otelServiceName`
- `levelname`
- `message`

## File Locations

- **Corrected YAML**: `documents/collector-fixed.yaml` (in this jRetireWise repo)
- **Apply to**: `cluster/infrastructure/monitoring/opentelementry-collector/collector.yaml` (in your home-lab repo)

## What This Enables

Once deployed, you'll have:

✅ **Filelog Receiver** - Reads pod container logs from `/var/log/containers/`
✅ **JSON Parsing** - Automatically parses JSON log entries
✅ **Kubernetes Resource Detection** - Adds pod name, namespace, container name automatically
✅ **Log Batching** - Batches 100 logs or 10 seconds before sending
✅ **Attribute Enrichment** - Adds environment and cluster labels
✅ **Splunk Export** - Sends logs to Splunk HEC with full trace context

## Troubleshooting

### Pod crashing with "invalid keys: filelog"
- Ensure image is upgraded: `otel/opentelemetry-collector-contrib:latest` or 0.97.0+
- Verify the configuration syntax is correct (no extra spaces, proper YAML)
- Check that filelog uses correct field names: `multiline_type` and `multiline_line_start_pattern` (not `multiline_parser`)

### Pod crashing with "has invalid keys: exclude_paths, include_paths, multiline_parser"
- This error means you're using old filelog syntax
- Update to new syntax:
  - `include` instead of `include_paths`
  - `exclude` instead of `exclude_paths`
  - `multiline_type: json` and `multiline_line_start_pattern: '^\{'` instead of `multiline_parser`
- Use the corrected `collector-fixed.yaml` from this repository

### Pod crashing with "has invalid keys: address" in service.telemetry
- Remove the `service.telemetry.metrics` section entirely
- The collector doesn't need explicit metrics telemetry configuration

### Pod crashing with "unknown type: resource_detection"
- Verify processor name is `resourcedetection` (no underscore)
- Check it's listed in the logs pipeline: `processors: [batch, attributes, resourcedetection]`

### Filelog receiver not reading logs
- Verify volume mounts are correct (varlog and varlibdockercontainers)
- Check include_paths match your application names
- Verify pod has read permission to /var/log/containers

### Logs not appearing in Splunk
- Check Splunk HEC endpoint is reachable from collector pod
- Verify SPLUNK_HEC_TOKEN secret is set correctly
- Search with sourcetype: `sourcetype="otel:logs"`
- Check Splunk index "otel_logging" has received events

## Next Steps

1. Update your home-lab collector.yaml with the corrected configuration
2. Commit and push the changes
3. Monitor the collector pod logs for successful startup
4. Generate test requests to jretirewise
5. Verify logs appear in Splunk with trace context

Once working, jretirewise logs will flow to Splunk with full correlation to traces and metrics via trace IDs!

## Reference

- [OTEL Collector Filelog Receiver Docs](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/filelogreceiver)
- [OTEL Collector Resourcedetection Processor Docs](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/resourcedetectionprocessor)
