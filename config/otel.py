"""
OpenTelemetry initialization and configuration for jRetireWise.
"""

import os
import logging
import atexit
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter

logger = logging.getLogger(__name__)

_otel_initialized = False
_tracer_provider = None
_meter_provider = None


def initialize_otel():
    """
    Initialize OpenTelemetry SDK with OTLP exporters for traces and metrics.

    This sets up:
    - Distributed tracing via OTLP to OTEL collector (gRPC port 4317)
    - Metrics export via OTLP to OTEL collector (gRPC port 4317)
    - Automatic instrumentation with trace context injection

    Logging Pattern:
    - LoggingInstrumentor captures all Python logs via logging module
    - Injects trace context (trace_id, span_id) into each log record as JSON fields
    - Outputs logs as JSON to stdout with full trace context
    - Pod logs collected by Kubernetes container logging
    - Logs ingested to OTEL collector via filelog receiver configured in collector YAML
    """
    global _otel_initialized, _tracer_provider, _meter_provider

    # Skip if already initialized
    if _otel_initialized:
        return _tracer_provider, _meter_provider

    # Get configuration from environment
    otel_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
    service_name = os.environ.get('OTEL_SERVICE_NAME', 'jretirewise')
    service_version = os.environ.get('OTEL_SERVICE_VERSION', '1.0.0')

    logger.info(f"Initializing OpenTelemetry with endpoint: {otel_endpoint}, service: {service_name}")

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": service_version,
        "service.namespace": "jretirewise",
    })

    # Initialize Tracer Provider
    logger.info("Creating gRPC OTLP span exporter...")
    trace_exporter = OTLPSpanExporter(
        endpoint=otel_endpoint,
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    logger.info("gRPC OTLP span exporter created and added to tracer provider")

    # Add console exporter for debugging in development only
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    if debug_mode:
        logger.info("DEBUG mode enabled, adding console span exporter")
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Set tracer provider globally
    trace.set_tracer_provider(tracer_provider)
    logger.info("Global tracer provider set successfully")

    # Initialize Meter Provider
    logger.info("Creating gRPC OTLP metric exporter...")
    metric_exporter = OTLPMetricExporter(
        endpoint=otel_endpoint,
    )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    logger.info("gRPC OTLP metric exporter created")

    # Add console exporter for debugging in development only
    metric_readers = [metric_reader]
    if debug_mode:
        logger.info("DEBUG mode enabled, adding console metric exporter")
        console_metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        metric_readers.append(console_metric_reader)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
    )

    metrics.set_meter_provider(meter_provider)
    logger.info("Global meter provider set successfully")

    # Enable automatic instrumentation
    logger.info("Enabling automatic instrumentation for Django, Celery, Requests, SQLAlchemy, Psycopg2, Logging")
    DjangoInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    LoggingInstrumentor().instrument()
    logger.info("All instrumentors enabled successfully")

    # Register shutdown hook to flush spans/metrics/logs on exit
    atexit.register(_shutdown_otel)
    logger.info("Registered shutdown hook for graceful OTEL shutdown")

    _tracer_provider = tracer_provider
    _meter_provider = meter_provider
    _otel_initialized = True

    logger.info("OpenTelemetry initialization completed successfully")
    return tracer_provider, meter_provider


def _shutdown_otel():
    """
    Graceful shutdown of OpenTelemetry providers.
    Ensures all spans and metrics are flushed before shutdown.
    """
    global _tracer_provider, _meter_provider

    try:
        if _tracer_provider is not None:
            logger.info("Flushing OpenTelemetry trace provider...")
            _tracer_provider.force_flush(timeout_millis=5000)
            logger.info("OpenTelemetry trace provider flushed")
    except Exception as e:
        logger.error(f"Error flushing trace provider: {e}", exc_info=True)

    try:
        if _meter_provider is not None:
            logger.info("Flushing OpenTelemetry meter provider...")
            _meter_provider.force_flush(timeout_millis=5000)
            logger.info("OpenTelemetry meter provider flushed")
    except Exception as e:
        logger.error(f"Error flushing meter provider: {e}", exc_info=True)


def initialize_otel_for_celery():
    """
    Initialize OpenTelemetry for Celery worker processes.
    Called from Celery worker initialization.
    """
    return initialize_otel()
