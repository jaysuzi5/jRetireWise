FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files as root (before switching to appuser)
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/media && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py shell -c "from django.core.management import call_command; call_command('migrate', verbosity=0)" || exit 1

# Expose port
EXPOSE 8000

# Run application with OpenTelemetry auto instrumentation
# Sends traces and metrics to OTLP collector via environment variable OTEL_EXPORTER_OTLP_ENDPOINT
# Logs are sent via LoggingInstrumentor in application code
CMD ["opentelemetry-instrument", \
     "--traces_exporter", "otlp", \
     "--metrics_exporter", "otlp", \
     "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
