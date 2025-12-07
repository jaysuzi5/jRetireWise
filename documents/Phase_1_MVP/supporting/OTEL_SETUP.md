# OpenTelemetry Setup for jRetireWise Django Application

## Overview

This document explains how OpenTelemetry (OTEL) is configured for the jRetireWise Django application to collect traces, metrics, and logs and send them to an OTEL collector.

## Architecture

### How it Works

1. **Dockerfile**: Uses `opentelemetry-instrument` CLI wrapper to start gunicorn
2. **Environment Variables**: OTEL configuration via Kubernetes ConfigMap
3. **Manual Initialization**: `config/otel.py` provides additional setup for Django-specific instrumentation
4. **WSGI Application**: `config/wsgi.py` calls `initialize_otel()` on startup

### Signal Types

- **Traces**: Distributed tracing via OTLP gRPC to port 4317
- **Metrics**: Application metrics via OTLP gRPC to port 4317
- **Logs**: Application logs via OTLP gRPC to port 4317 (when using `opentelemetry-instrument`)

## Configuration

### Dockerfile

The application is started with the `opentelemetry-instrument` CLI wrapper:

```dockerfile
CMD ["opentelemetry-instrument", \
     "--logs_exporter", "otlp", \
     "--traces_exporter", "otlp", \
     "--metrics_exporter", "otlp", \
     "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

This wrapper:
- Automatically instruments the application without code changes
- Exports all three signal types (traces, metrics, logs) to OTLP endpoint
- Works alongside manual instrumentation in `config/otel.py`

### Environment Variables (Kubernetes ConfigMap)

Add these to your Kubernetes ConfigMap:

```yaml
# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector-collector.monitoring.svc.cluster.local:4317"
OTEL_SERVICE_NAME: "jretirewise"
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true"
OTEL_SDK_DISABLED: "false"
```

**Key settings:**
- `OTEL_EXPORTER_OTLP_ENDPOINT`: gRPC endpoint of your OTEL collector (port 4317 for gRPC)
- `OTEL_SERVICE_NAME`: Service identifier in telemetry data
- `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED`: Enables automatic log instrumentation
- `OTEL_SDK_DISABLED`: Set to "false" to enable OTEL

### Kubernetes Deployment

The deployment manifest includes environment variables for OTEL:

```yaml
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  valueFrom:
    configMapKeyRef:
      name: jretirewise-config
      key: OTEL_EXPORTER_OTLP_ENDPOINT
- name: OTEL_SERVICE_NAME
  valueFrom:
    configMapKeyRef:
      name: jretirewise-config
      key: OTEL_SERVICE_NAME
- name: OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
  valueFrom:
    configMapKeyRef:
      name: jretirewise-config
      key: OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
```

### Django Settings (config/settings.py)

OTEL configuration is read from environment:

```python
# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT = env('OTEL_EXPORTER_OTLP_ENDPOINT', default='http://localhost:4318')
OTEL_SERVICE_NAME = 'jretirewise'
OTEL_SERVICE_VERSION = '1.0.0'
```

### WSGI Application (config/wsgi.py)

Manual initialization for Django-specific instrumentation:

```python
from config.otel import initialize_otel
initialize_otel()

application = get_wsgi_application()
```

This initializes:
- Trace provider and OTLP exporter
- Metrics provider and OTLP exporter
- Auto-instrumentation for Django, Celery, Requests, SQLAlchemy, Psycopg2, Logging

## What Gets Instrumented

### Automatic Instrumentation

When the application starts, the following are automatically instrumented:

1. **Django** - HTTP requests, responses, view execution
2. **Celery** - Task execution, task queues
3. **Requests** - HTTP client calls
4. **SQLAlchemy/Psycopg2** - Database queries
5. **Logging** - All Python logs with trace context injected

### Trace Context

All logs and events include:
- `trace_id` - Unique trace identifier
- `span_id` - Current span identifier
- `service.name` - Service name (jretirewise)
- `service.version` - Service version (1.0.0)

## Local Development

### Without Docker

To run locally with OTEL enabled:

```bash
# Set environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="jretirewise-dev"
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"

# Install opentelemetry-instrument
pip install opentelemetry-distro opentelemetry-exporter-otlp

# Run with instrumentation
opentelemetry-instrument python manage.py runserver
```

### With Docker Compose

The `docker-compose.yml` should include the OTEL collector service. When you rebuild and run:

```bash
docker-compose up --build
```

The application will automatically send telemetry to the collector.

## Troubleshooting

### Check OTEL is Enabled

1. Look for these log messages on startup:
   ```
   OpenTelemetry Trace Provider initialized with endpoint: http://otel-collector-collector.monitoring.svc.cluster.local:4317
   OpenTelemetry Log Provider initialized with endpoint: http://otel-collector-collector.monitoring.svc.cluster.local:4317
   ```

2. Verify environment variables in the container:
   ```bash
   kubectl exec -it <pod-name> -n jretirewise -- env | grep OTEL
   ```

### Check Collector Connectivity

1. Verify the collector is running and accessible:
   ```bash
   kubectl get pods -n monitoring | grep otel
   ```

2. Test connectivity from the pod:
   ```bash
   kubectl exec -it <pod-name> -n jretirewise -- \
     curl -v otel-collector-collector.monitoring.svc.cluster.local:4317
   ```

### Enable Debug Logging

Set DEBUG=true in environment to see console span exports:

```yaml
DEBUG: "true"  # Enables console span and metric exporters
```

## Comparison with Other Services

This setup follows the same pattern as your other OTEL-instrumented services (like "book"):

| Component | Your API | Django App |
|-----------|----------|-----------|
| CLI Wrapper | `opentelemetry-instrument` | `opentelemetry-instrument` |
| Logs Exporter | `--logs_exporter otlp` | `--logs_exporter otlp` |
| Traces Exporter | `--traces_exporter otlp` | `--traces_exporter otlp` |
| Endpoint | Port 4317 (gRPC) | Port 4317 (gRPC) |
| Service Name | From OTEL_SERVICE_NAME env | From OTEL_SERVICE_NAME env |
| Log Auto-instrumentation | OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED | OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED |

## Dependencies

Required Python packages (in requirements.txt):

```
opentelemetry-api>=0.47b0
opentelemetry-sdk>=0.47b0
opentelemetry-instrumentation>=0.47b0
opentelemetry-instrumentation-django>=0.47b0
opentelemetry-instrumentation-celery>=0.47b0
opentelemetry-instrumentation-requests>=0.47b0
opentelemetry-instrumentation-sqlalchemy>=0.47b0
opentelemetry-instrumentation-psycopg2>=0.47b0
opentelemetry-instrumentation-logging>=0.47b0
opentelemetry-exporter-otlp>=0.47b0
opentelemetry-exporter-otlp-proto-grpc>=0.47b0
```

## Next Steps

1. **Build and test locally**:
   ```bash
   docker-compose up --build
   ```

2. **Verify telemetry in collector**: Check your OTEL collector logs to confirm signals are being received

3. **Query telemetry**: Use your OTEL backend (Jaeger, Tempo, etc.) to query traces and logs

4. **Monitor Celery**: Celery tasks now have distributed traces automatically

5. **Custom metrics**: Add custom metrics in your application code:
   ```python
   from opentelemetry import metrics
   meter = metrics.get_meter(__name__)
   counter = meter.create_counter("custom.requests")
   counter.add(1)
   ```

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Django](https://opentelemetry.io/docs/instrumentation/python/libraries/django/)
- [OTLP Protocol](https://opentelemetry.io/docs/reference/specification/protocol/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
