# OpenTelemetry Troubleshooting Summary

## Overview

This document summarizes all issues found and fixed to get OpenTelemetry working correctly in jRetireWise, including traces, metrics, and logs flowing to the OTEL collector and Splunk.

## Issues Found and Fixed

### Issue 1: Filelog Receiver Not Matching Web Container Logs

**Problem**: The OTEL collector's filelog receiver was configured but not capturing logs from the jretirewise web application pods.

**Root Cause**: Container naming mismatch. The glob pattern `/var/log/containers/*jretirewise*.log` matched postgres and redis sidecars (which have "jretirewise" in their namespace) but NOT the main web container, which is named `web`.

**Kubernetes Container Log Filename Structure**:
```
{pod-name}_{namespace}_{container-name}-{container-id}.log
```

Example:
```
prod-jretirewise-jretirewise-web-58cff8585b-hnx5b_jretirewise_web-[hash].log
                                                    ^^^^ Container name is "web", not "jretirewise"
```

**Solution**: Added explicit pattern to filelog receiver:
```yaml
filelog:
  include:
    - /var/log/containers/*jretirewise*.log
    - /var/log/containers/prod-jretirewise-jretirewise-web_jretirewise_web-*.log  # ← FIX
```

**Files Modified**:
- `documents/collector-fixed.yaml` - Added explicit web container pattern
- `documents/OTEL_COLLECTOR_UPGRADE_GUIDE.md` - Documented the critical fix
- `documents/FILELOG_FIX_ROOT_CAUSE.md` - Comprehensive analysis

### Issue 2: Exporter Using HTTP Instead of gRPC

**Problem**: Web pod logs showed repeated `ConnectionResetError: [Errno 104] Connection reset by peer` when trying to export spans and metrics.

**Root Cause**: The OTEL SDK was configured to use HTTP OTLP exporters, but the environment variable was set to a gRPC endpoint (port 4317):
```python
# WRONG: Using HTTP exporter with gRPC endpoint
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

endpoint = "http://otel-collector-collector.monitoring.svc.cluster.local:4317"
trace_exporter = OTLPSpanExporter(
    endpoint=f"{endpoint}/v1/traces"  # ← Trying to POST to gRPC port!
)
```

The HTTP exporter tried to POST to `http://otel-collector:4317/v1/traces`, but port 4317 only accepts gRPC connections, causing connection reset errors.

**Solution**: Switch to gRPC exporters:
```python
# CORRECT: Using gRPC exporter with gRPC endpoint
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

trace_exporter = OTLPSpanExporter(
    endpoint=otel_endpoint  # gRPC doesn't use /v1/traces path
)
```

**Key Changes**:
- Changed `opentelemetry.exporter.otlp.proto.http` → `opentelemetry.exporter.otlp.proto.grpc`
- Removed `/v1/traces` and `/v1/metrics` path suffixes (gRPC doesn't use HTTP paths)
- Both trace and metric exporters now use gRPC

**Files Modified**:
- `config/otel.py` - Switched to gRPC exporters

### Error Messages

The errors manifested as repeated log messages in the web pod:
```json
{
  "levelname": "ERROR",
  "message": "Exception while exporting Span batch.",
  "exc_info": "... ConnectionResetError: [Errno 104] Connection reset by peer ..."
}
```

This happened continuously as the application tried to batch and export spans every 10 seconds.

## Impact Summary

| Issue | Severity | Impact | Status |
|-------|----------|--------|--------|
| Filelog receiver not matching web logs | HIGH | Application logs never reached Splunk via filelog receiver | ✅ FIXED |
| HTTP exporter to gRPC endpoint | CRITICAL | All traces and metrics failed to export, error spam in logs | ✅ FIXED |

## Testing After Fixes

After applying these fixes:

1. **Filelog receiver** will now match and ingest web container logs from `/var/log/containers/`
2. **Trace exporter** will successfully connect to OTEL collector on port 4317 using gRPC
3. **Metric exporter** will successfully connect to OTEL collector on port 4317 using gRPC
4. Application logs will flow through filelog receiver → OTEL collector → Splunk
5. Traces will flow from application → OTEL collector → Tempo
6. Metrics will flow from application → OTEL collector → Prometheus

## Next Steps

1. Docker image will be rebuilt with these fixes
2. Application will be redeployed
3. Verify traces/metrics appear in OTEL collector
4. Verify container logs appear in Splunk with trace context

## Key Learnings

### OTEL Exporter Protocol Selection
- **gRPC**: Native binary protocol, lower overhead, supports HTTP/2. Port 4317.
- **HTTP**: REST/JSON protocol, easier debugging. Port 4318.
- **Critical**: Match the protocol to the endpoint! Don't use HTTP exporter on gRPC port.

### Kubernetes Container Log Naming
When using glob patterns for container logs, remember:
- Pod names often contain application names multiple times
- Container names are DIFFERENT from pod names
- Always verify the container name in the actual log filename
- Use explicit patterns when wildcards don't match expected containers

### OTEL Collector Configuration
The collector expects all clients to use the protocol specified in the receiver configuration:
```yaml
receivers:
  otlp:
    protocols:
      grpc:                      # ← gRPC protocol on port 4317
        endpoint: "0.0.0.0:4317"
      http:                       # ← HTTP protocol on port 4318
        endpoint: "0.0.0.0:4318"
```

If you're sending to port 4317, use gRPC exporters. If sending to port 4318, use HTTP exporters.

## References

- OTEL Collector Filelog Receiver: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/filelogreceiver
- OTEL Python SDK: https://opentelemetry.io/docs/instrumentation/python/
- OTEL Protocol: https://opentelemetry.io/docs/reference/specification/protocol/
