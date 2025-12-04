"""
OpenTelemetry initialization and configuration for jRetireWise.
"""

import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter


def initialize_otel():
    """
    Initialize OpenTelemetry SDK with OTLP exporters.
    This sets up tracing, metrics, and logging instrumentation.

    NOTE: Logs export disabled due to SDK version constraints.
    The LoggingInstrumentor still captures Python logs, which are visible
    in pod stderr and can be scraped by log collection systems.
    Structured log export to OTEL will require SDK v1.27.0+ with separate logs package.
    """

    # Get configuration from environment
    otel_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
    service_name = os.environ.get('OTEL_SERVICE_NAME', 'jretirewise')
    service_version = os.environ.get('OTEL_SERVICE_VERSION', '1.0.0')

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": service_version,
        "service.namespace": "jretirewise",
    })

    # Initialize Tracer Provider
    trace_exporter = OTLPSpanExporter(
        endpoint=f"{otel_endpoint}/v1/traces",
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    # Also add console exporter for debugging
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Only set if not already set
    try:
        trace.set_tracer_provider(tracer_provider)
    except RuntimeError:
        # TracerProvider already set, skip
        pass

    # Initialize Meter Provider
    metric_exporter = OTLPMetricExporter(
        endpoint=f"{otel_endpoint}/v1/metrics",
    )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)

    # Also add console exporter for debugging
    console_metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader, console_metric_reader],
    )

    metrics.set_meter_provider(meter_provider)

    # Enable automatic instrumentation
    DjangoInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    LoggingInstrumentor().instrument()

    return tracer_provider, meter_provider


def initialize_otel_for_celery():
    """
    Initialize OpenTelemetry for Celery worker processes.
    Called from Celery worker initialization.
    """
    return initialize_otel()
