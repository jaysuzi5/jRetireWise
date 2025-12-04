# Application Log Collection Setup for jRetireWise

## Overview

This document explains how to collect application logs from jRetireWise that are written to stdout with full OpenTelemetry trace context. It provides multiple approaches depending on your infrastructure.

## Current State

**jretirewise Application:**
- ✅ Logs are being written to stdout as JSON with full trace context
- ✅ Each log includes: `otelTraceID`, `otelSpanID`, `otelServiceName`
- ✅ Traces and metrics are flowing to OTEL collector via OTLP (gRPC port 4317)
- ❌ Pod stdout logs are NOT being collected to OTEL/Splunk

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

## Solution Approaches

### Option 1: Splunk Native Kubernetes Logging (RECOMMENDED - Simplest)

Use Splunk's native Kubernetes logging to collect pod container logs. This requires no changes to your OTEL collector.

**Advantages:**
- ✅ No collector configuration needed
- ✅ Works immediately with current setup
- ✅ Logs arrive in Splunk with full trace context
- ✅ No additional components to maintain

**Implementation Steps:**

1. **Install Splunk Add-on for Kubernetes** (if not already installed)
   - Splunk Web > Settings > Manage Apps > Browse more apps
   - Search for "Kubernetes" and install the official Splunk Add-on

2. **Configure Kubernetes data input**
   - Settings > Data inputs > HTTP Event Collector
   - Create new HEC token with sourcetype `json`

3. **Enable container logs collection**
   - Settings > Add data > Monitor Kubernetes
   - Configure to collect pod logs from your cluster
   - Map to your HEC token

4. **Search in Splunk**
   ```
   source="kubernetes" sourcetype="json" service="jretirewise"
   | stats count by levelname, message
   ```

**References:**
- [Splunk Add-on for Kubernetes](https://splunkbase.splunk.com/app/3877)
- [Splunk Kubernetes Logging](https://docs.splunk.com/Documentation/AddOnforKubernetes/latest/)

---

### Option 2: Fluent Bit / Fluentd for Log Collection

Deploy Fluent Bit as a DaemonSet to collect pod logs and forward to Splunk HEC.

**Advantages:**
- ✅ Lightweight (Fluent Bit) or feature-rich (Fluentd)
- ✅ Flexible log parsing and enrichment
- ✅ Direct integration with Splunk HEC
- ✅ Works with existing OTEL collector

**Implementation:**

1. **Deploy Fluent Bit DaemonSet**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: fluent-bit-config
     namespace: monitoring
   data:
     fluent-bit.conf: |
       [SERVICE]
           Flush 5
           Daemon Off
           Log_Level info
           Parsers_File parsers.conf

       [INPUT]
           Name tail
           Path /var/log/containers/*jretirewise*.log
           Parser json
           Tag kube.*

       [OUTPUT]
           Name splunk
           Match *
           Host splunk.example.com
           Port 8088
           Token ${SPLUNK_HEC_TOKEN}
           Send_Raw on
   ---
   apiVersion: apps/v1
   kind: DaemonSet
   metadata:
     name: fluent-bit
     namespace: monitoring
   spec:
     selector:
       matchLabels:
         app: fluent-bit
     template:
       metadata:
         labels:
           app: fluent-bit
       spec:
         containers:
         - name: fluent-bit
           image: fluent/fluent-bit:latest
           volumeMounts:
           - name: varlog
             mountPath: /var/log
             readOnly: true
           - name: varlibdockercontainers
             mountPath: /var/lib/docker/containers
             readOnly: true
           - name: config
             mountPath: /fluent-bit/etc/
         volumes:
         - name: varlog
           hostPath:
             path: /var/log
         - name: varlibdockercontainers
           hostPath:
             path: /var/lib/docker/containers
         - name: config
           configMap:
             name: fluent-bit-config
   ```

2. **Configure Splunk HEC endpoint in values**

3. **Verify logs in Splunk**

**References:**
- [Fluent Bit Documentation](https://docs.fluentbit.io/)
- [Fluent Bit Splunk Output](https://docs.fluentbit.io/manual/pipeline/outputs/splunk)

---

### Option 3: Upgrade OTEL Collector to Support Filelog Receiver

If you want to use the OTEL Collector's filelog receiver, you need to upgrade to a version that includes it.

**Issue with Current Setup:**
- Your collector image (0.96.0) doesn't have `filelog` receiver compiled in
- Error: `has invalid keys: filelog`

**Solution:**

1. **Upgrade OTEL Collector image to contrib version with filelog support**

   In your `collector.yaml`, update the image:
   ```yaml
   image: otel/opentelemetry-collector-contrib:latest  # or specific version like 0.97.0+
   ```

2. **Fix processor name in configuration**

   Change `resource_detection` to `resourcedetection` (one word):
   ```yaml
   processors:
     batch:
       send_batch_size: 100
       timeout: 10s
     resourcedetection:  # Changed from resource_detection
       detectors: [kubernetes]
     attributes:
       actions:
         - key: environment
           value: production
           action: insert
   ```

3. **Add filelog receiver configuration**
   ```yaml
   receivers:
     otlp:
       protocols:
         grpc:
           endpoint: 0.0.0.0:4317
         http:
           endpoint: 0.0.0.0:4318

     filelog:
       include_paths:
         - /var/log/containers/*jretirewise*.log
         - /var/log/containers/*todo*.log
         - /var/log/containers/*emporia*.log
       exclude_paths:
         - /var/log/containers/*_kube-system_*.log
         - /var/log/containers/*_kube-public_*.log
   ```

4. **Update service pipeline to include filelog**
   ```yaml
   service:
     pipelines:
       logs:
         receivers: [otlp, filelog]
         processors: [batch, attributes]
         exporters: [splunk_hec, debug]
   ```

5. **Restart collector**
   ```bash
   kubectl rollout restart deployment/otel-collector-collector -n monitoring
   ```

**Note:** This approach requires upgrading your collector image, which may impact other parts of your monitoring setup.

---

## Recommendation

**Use Option 1 (Splunk Native Kubernetes Logging)** because:
- ✅ Simplest implementation
- ✅ No changes to existing OTEL collector
- ✅ Splunk has native support for Kubernetes logs
- ✅ Works immediately with current setup
- ✅ Logs already have trace context in JSON fields

**Only use Option 2 or 3 if you need:**
- Advanced log filtering/transformation before sending to Splunk
- Specific parsing not available in Splunk's native collector
- Use of OTEL collector as single log collection point

---

## Verification Steps

### For Option 1 (Splunk Native):
1. In Splunk, search: `source="kubernetes" service="jretirewise"`
2. Verify you see JSON logs with trace context fields
3. Check that fields like `otelTraceID`, `otelSpanID` are searchable

### For Option 2 (Fluent Bit):
1. Check DaemonSet is running: `kubectl get ds -n monitoring`
2. Verify logs flowing: `kubectl logs -n monitoring -l app=fluent-bit`
3. Search in Splunk: `source="fluent-bit" service="jretirewise"`

### For Option 3 (Upgraded Collector):
1. Check collector is running: `kubectl get pods -n monitoring`
2. Verify filelog receiver: `kubectl logs -n monitoring otel-collector-collector-* | grep filelog`
3. Search in Splunk: `source="otel-collector" service="jretirewise"`

---

## Troubleshooting

### Logs not appearing in Splunk
1. Verify Splunk HEC is accepting data from collector pods
2. Check HEC token has correct permissions
3. Verify sourcetype is set to `json` for proper parsing
4. Search with broader criteria: `service="jretirewise"` (without source filter)

### Wrong processor name error
- Error: `unknown type: "resource_detection"`
- Fix: Change to `resourcedetection` (no underscore)

### Filelog receiver not recognized
- Error: `has invalid keys: filelog`
- Cause: Current collector image doesn't include filelog
- Fix: Use Option 1 or upgrade collector image to contrib version

---

## Summary

| Approach | Effort | Reliability | Recommended |
|----------|--------|-------------|------------|
| **Option 1: Splunk Native** | Low | High | ✅ Yes |
| **Option 2: Fluent Bit** | Medium | High | For advanced filtering |
| **Option 3: Upgrade Collector** | Medium | High | If centralizing all collection |

Start with **Option 1** - it requires no infrastructure changes and works with your current setup immediately.
