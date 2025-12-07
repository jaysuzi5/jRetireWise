import os
import logging

from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider, get_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

def setup_opentelemetry():
    logger = logging.getLogger()

    # Check if LoggerProvider already exists (e.g., from opentelemetry-instrument)
    logger_provider = get_logger_provider()
    
    if logger_provider is None:
        # No provider exists, create a new one
        otlp_export_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if not otlp_export_endpoint:
            logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping OpenTelemetry log setup")
            return

        # add resource metadata to logs
        resource = Resource.create(attributes={
            "service.name": "jRetireWise"
        })
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        # define the exporter to send logs to the observability backend 
        log_exporter = OTLPLogExporter(endpoint=otlp_export_endpoint)
        # register it with the global provider
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )

    # configure the python logging module to support OTel by registering the handler
    handler = LoggingHandler(level="INFO", logger_provider=logger_provider)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # inject trace context into logs
    LoggingInstrumentor().instrument(set_logging_format=True)

    logger.info("OpenTelemetry logging is configured.")
