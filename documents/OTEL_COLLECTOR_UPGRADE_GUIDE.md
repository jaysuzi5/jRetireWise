# OTEL Collector Upgrade Guide - Filelog Receiver Integration

## Overview

This guide provides the corrected OpenTelemetry Collector configuration with the filelog receiver for collecting jretirewise pod logs.

## What Was Wrong

Your current configuration had two critical issues:

### Issue 1: Incorrect Filelog Configuration (Field Names)
```yaml
# WRONG - Using incorrect field names
filelog:
  include_paths:    # ❌ WRONG
    - /var/log/containers/*jretirewise*.log
  exclude_paths:    # ❌ WRONG
    - /var/log/containers/*_kube-system_*.log
  multiline_parser: # ❌ WRONG
    type: json
```

The OTEL Collector filelog receiver requires:
- `include` (not `include_paths`)
- `exclude` (not `exclude_paths`)
- `multiline` block with `line_start_pattern` (not `multiline_parser`)
- `operators` array with `json_parser` type for JSON log parsing

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

### 2. Filelog Receiver Fixed (Correct Syntax)
```yaml
# NOW CORRECT - Proper syntax for OTEL Collector filelog receiver
filelog:
  include:                                  # ✅ Correct field name
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/*todo*.log
    - /var/log/containers/*emporia*.log
  exclude:                                  # ✅ Correct field name
    - /var/log/containers/*_kube-system_*.log
    - /var/log/containers/*_kube-public_*.log
    - /var/log/containers/*_kube-node-lease_*.log
  multiline:                                # ✅ Nested block (not root field)
    line_start_pattern: '^\{'               # ✅ Correct pattern syntax
  operators:                                # ✅ Added operators for JSON parsing
    - type: json_parser
      timestamp:
        parse_from: attributes.asctime
        layout: '%Y-%m-%d %H:%M:%S,%f'
      severity:
        parse_from: attributes.levelname
```

Key updates:
- `include` replaces `include_paths` (simpler field name)
- `exclude` replaces `exclude_paths` (simpler field name)
- `multiline` is a nested block with `line_start_pattern` inside
- `operators` array with `json_parser` type extracts timestamp and severity fields from JSON logs

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

### Pod crashing with "has invalid keys: exclude_paths, include_paths, multiline_type, multiline_line_start_pattern"
- This error means the filelog receiver configuration syntax is incorrect
- The collector is rejecting these field names because they don't exist in the current schema
- Update to correct syntax:
  - `include` instead of `include_paths` (simpler field name)
  - `exclude` instead of `exclude_paths` (simpler field name)
  - `multiline:` nested block with `line_start_pattern: '^\{'` inside (not `multiline_type` or `multiline_line_start_pattern`)
  - Add `operators:` array with `type: json_parser` for JSON parsing
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
