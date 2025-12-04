# OTEL Collector Filelog Receiver Setup

## Overview

This document explains how to configure your OpenTelemetry Collector to receive and process logs from Kubernetes pod containers using the filelog receiver. This enables collection of application logs written to stdout/stderr with full trace context.

## Current State

**jretirewise Application:**
- ✅ Logs are being written to stdout as JSON with full trace context
- ✅ Each log includes: `otelTraceID`, `otelSpanID`, `otelServiceName`
- ✅ Traces and metrics are flowing to OTEL collector via OTLP (gRPC port 4317)
- ❌ Logs are NOT being collected from pod stdout

**Example Log Entry:**
```json
{
  "asctime": "2025-12-04 16:56:08,394",
  "name": "jretirewise",
  "levelname": "INFO",
  "message": "GET / - Status: 302 - 11.06ms",
  "otelSpanID": "ccc5261cea74e028",
  "otelTraceID": "34dd33cd00f19800b16e6cc8bfe64973",
  "otelTraceSampled": true,
  "otelServiceName": "jretirewise"
}
```

## Solution: Add Filelog Receiver to OTEL Collector

The filelog receiver is part of OpenTelemetry Collector Contrib and reads log files from the container filesystem, making it perfect for collecting Kubernetes pod logs.

### Step 1: Update OTEL Collector ConfigMap

Edit your OTEL collector configuration file in your home-lab repository (`cluster/infrastructure/monitoring/opentelementry-collector/collector.yaml`) and add the filelog receiver to the receivers section:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # ADD THIS SECTION - Filelog receiver for Kubernetes pod logs
  filelog:
    include_paths:
      - /var/log/containers/*jretirewise*.log
      - /var/log/containers/*todo*.log
      - /var/log/containers/*emporia*.log
    exclude_paths:
      - /var/log/containers/*_kube-system_*.log
      - /var/log/containers/*_kube-public_*.log
      - /var/log/containers/*_kube-node-lease_*.log
    multiline_parser:
      type: json
      parse_from: body
    resource_detection:
      enabled: true
```

### Step 2: Update Service Pipelines

Add the filelog receiver to your service pipelines section:

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [tempo]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]

    # ADD THIS PIPELINE - Process logs from filelog receiver
    logs:
      receivers: [otlp, filelog]
      processors: [batch, attributes]
      exporters: [splunk_hec, debug]
```

### Step 3: Configure Log Processors (Optional but Recommended)

Add an attributes processor to enrich logs with Kubernetes metadata:

```yaml
processors:
  batch:
    send_batch_size: 100
    timeout: 10s

  # Optional: Attributes processor to add custom attributes to logs
  attributes:
    actions:
      - key: environment
        value: production
        action: insert
      - key: cluster
        value: home-lab
        action: insert

  # Add this if you want to parse trace context from logs
  resource_detection:
    detectors:
      - kubernetes
```

### Step 4: Deployment Requirements

The OTEL Collector pod needs permission to read Kubernetes container logs. Ensure your collector deployment has:

1. **Volume mounts for Kubernetes logs:**
```yaml
volumes:
  - name: varlog
    hostPath:
      path: /var/log
  - name: varlibdockercontainers
    hostPath:
      path: /var/lib/docker/containers

volumeMounts:
  - name: varlog
    mountPath: /var/log
    readOnly: true
  - name: varlibdockercontainers
    mountPath: /var/lib/docker/containers
    readOnly: true
```

2. **Appropriate RBAC permissions** (if using containerd or other runtimes):
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-collector-logs
rules:
  - apiGroups: [""]
    resources: ["pods", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-collector-logs
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-collector-logs
subjects:
  - kind: ServiceAccount
    name: otel-collector
    namespace: monitoring
```

## Configuration Options Explained

### Filelog Receiver Options

- **include_paths**: Glob patterns for log files to include
  - Pattern: `/var/log/containers/*jretirewise*.log` captures all jretirewise pod logs
  - Use wildcards to match pod names and multiple services

- **exclude_paths**: Glob patterns for log files to exclude
  - Exclude system namespaces to reduce noise
  - Common patterns: kube-system, kube-public, kube-node-lease

- **multiline_parser**: Handles JSON parsing
  - `type: json` automatically detects and parses JSON log lines
  - Works perfectly with your pythonjsonlogger output

- **resource_detection**: Automatically detects Kubernetes resource attributes
  - Adds pod name, namespace, container name, etc. to log records

### Splunk HEC Exporter Configuration

Ensure your splunk_hec exporter is properly configured to receive logs:

```yaml
exporters:
  splunk_hec:
    endpoint: "https://your-splunk-instance:8088"
    token: "${SPLUNK_HEC_TOKEN}"
    source: "otel-collector"
    sourcetype: "json"
    ca_file: "/path/to/ca-cert.pem"  # if using self-signed cert
    skip_tls_verify: false
    max_content_length_logs: 100000
```

## Verification Steps

After updating your OTEL collector configuration:

1. **Restart the OTEL Collector:**
```bash
kubectl rollout restart deployment/otel-collector-collector -n monitoring
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=otel-collector -n monitoring --timeout=60s
```

2. **Check collector logs for filelog receiver startup:**
```bash
kubectl logs -n monitoring -l app.kubernetes.io/name=otel-collector -f | grep -i "filelog\|receiver"
```

3. **Generate test logs from jretirewise:**
```bash
curl -s http://192.168.86.229/jretirewise/ > /dev/null
```

4. **Check OTEL collector logs for ingested logs:**
```bash
kubectl logs -n monitoring otel-collector-collector-XXXXX --tail=100 | grep -i "jretirewise\|filelog"
```

5. **Verify logs appear in Splunk:**
- Search in Splunk: `source="otel-collector" sourcetype="json" service="jretirewise"`
- Look for logs with trace context fields: `otelTraceID`, `otelSpanID`

## Expected Result

Once filelog receiver is configured, you should see:

1. **In OTEL Collector logs:**
   - Filelog receiver successfully reading pod log files
   - Logs being parsed as JSON
   - Batched and sent to Splunk HEC

2. **In Splunk:**
   - jretirewise logs appearing in real-time
   - Full trace context available for correlation
   - Ability to search by trace ID and correlate with traces/metrics

3. **Example Splunk Query:**
```
source="otel-collector" service="jretirewise" | stats count by levelname, message
```

## Troubleshooting

### Logs not appearing in OTEL collector

1. **Check file permissions:**
   - OTEL collector pod needs read access to `/var/log/containers/`
   - Verify volume mounts are correct
   - Check pod is running with appropriate permissions

2. **Verify include_paths pattern:**
```bash
# List available pod log files
ls -la /var/log/containers/ | grep jretirewise
```

3. **Check OTEL collector configuration:**
```bash
kubectl describe configmap otel-collector-collector -n monitoring
```

### Logs not appearing in Splunk

1. **Verify Splunk HEC is configured:**
```bash
# Check Splunk HEC token is set in secrets
kubectl get secret -n monitoring otel-collector-secrets -o yaml | grep SPLUNK_HEC_TOKEN
```

2. **Test Splunk connectivity from collector:**
```bash
kubectl exec -it deployment/otel-collector-collector -n monitoring -- \
  curl -v -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \
  -X POST https://splunk-instance:8088/services/collector \
  -d '{"event":"test"}'
```

3. **Check Splunk HEC configuration:**
   - Verify token has correct permissions
   - Check HEC is accepting data from collector pod IP
   - Review Splunk indexes configuration

### Multiline or duplicate logs

1. **JSON parsing issues:**
   - Ensure logs are valid JSON format
   - Check pythonjsonlogger is properly configured
   - Verify no extra output is being written to stdout

2. **Adjust batch size if needed:**
```yaml
processors:
  batch:
    send_batch_size: 50  # Reduce for more frequent batches
    timeout: 5s          # Reduce timeout for lower latency
```

## Next Steps

1. Update your home-lab OTEL collector configuration with filelog receiver
2. Redeploy OTEL collector
3. Generate logs from jretirewise
4. Verify logs appear in OTEL collector logs
5. Verify logs appear in Splunk
6. Update any monitoring/alerting rules to include application logs

## References

- [OpenTelemetry Filelog Receiver Documentation](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/filelogreceiver/README.md)
- [Kubernetes Container Log Paths](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Splunk HEC Exporter Documentation](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/exporter/splunkhecexporter/README.md)
