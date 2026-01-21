"""
Telemetry and Observability Configuration.
Sets up OpenTelemetry tracing.
"""

import os

from fastapi import FastAPI

from logger import logger

# Global flag to check if OTel is initialized
_OTEL_INITIALIZED = False


def setup_telemetry(app: FastAPI, service_name: str = "purrfect-backend") -> None:
    """
    Configure OpenTelemetry tracing for the application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service for traces
    """
    global _OTEL_INITIALIZED

    # Skip if disabled via env
    if os.getenv("ENABLE_TELEMETRY", "false").lower() != "true":
        logger.info("Telemetry disabled (ENABLE_TELEMETRY!=true)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("OpenTelemetry packages not found. Skipping telemetry setup.")
        return

    try:
        # Define resource (service info)
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": os.getenv("APP_VERSION", "unknown"),
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

        # Set up provider
        provider = TracerProvider(resource=resource)

        # Configure exporter (Jaeger/OTLP)
        # Default to localhost for local dev if not specified
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

        # Add processor
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set global provider
        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        _OTEL_INITIALIZED = True
        logger.info(f"Telemetry initialized for {service_name} -> {otlp_endpoint}")

    except Exception as e:
        logger.error(f"Failed to initialize telemetry: {e}")


def get_tracer(name: str):
    """Safe wrapper to get tracer."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        # Return a dummy tracer if OTel not available
        class DummySpan:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class DummyTracer:
            def start_as_current_span(self, name):
                return DummySpan()

        return DummyTracer()
