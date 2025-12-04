"""
OpenTelemetry initialization and configuration for jRetireWise.
"""

import os
import logging
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


def initialize_otel():
    """
    Initialize OpenTelemetry SDK with OTLP exporters for traces and metrics.

    This sets up:
    - Distributed tracing via OTLP to OTEL collector (gRPC port 4317)
    - Metrics export via OTLP to OTEL collector (gRPC port 4317)
    - Automatic log instrumentation with trace context injection

    Logging Pattern (current):
    - LoggingInstrumentor automatically captures all Python logs via logging module
    - Injects trace context (trace_id, span_id) into each log record as JSON fields
    - Outputs logs as JSON to stdout with full trace context
    - Pod logs are collected by Kubernetes container logging
    - Logs should be ingested to OTEL collector via file/stdout receiver configured
      in the collector YAML (see home-lab repository for logs receiver configuration)

    Note on Log Export:
    - Direct SDK log export to OTEL collector requires OpenTelemetry logs API (v0.47b0+)
    - Current approach (v0.46b0) only captures logs with trace context to stdout
    - Stdout-based collection is reliable and works well with pod logging systems
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
        endpoint=otel_endpoint,
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

    # Add console exporter for debugging in development only
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    if debug_mode:
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Only set if not already set
    try:
        trace.set_tracer_provider(tracer_provider)
    except RuntimeError:
        # TracerProvider already set, skip
        pass

    # Initialize Meter Provider
    metric_exporter = OTLPMetricExporter(
        endpoint=otel_endpoint,
    )
    metric_reader = PeriodicExportingMetricReader(metric_exporter)

    # Add console exporter for debugging in development only
    metric_readers = [metric_reader]
    if debug_mode:
        console_metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        metric_readers.append(console_metric_reader)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
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
