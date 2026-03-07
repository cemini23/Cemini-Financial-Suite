"""
observability/tracing.py — Shared OpenTelemetry tracer initializer (Step 35d).

Call configure_tracing(service_name) once at FastAPI app startup.
Exports traces via OTLP gRPC to Grafana Alloy → Tempo.
Environment variables:
  OTEL_EXPORTER_OTLP_ENDPOINT  — default: http://alloy:4317
  OTEL_SERVICE_NAME             — overrides service_name arg if set
"""
import os
import logging

logger = logging.getLogger("cemini.tracing")

_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://alloy:4317")


def configure_tracing(service_name: str) -> None:
    """Initialize OTLP trace exporter for the given service.

    Safe to call in environments where opentelemetry packages are absent —
    logs a warning and returns without raising.
    """
    effective_name = os.getenv("OTEL_SERVICE_NAME", service_name)
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": effective_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=_OTLP_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("OpenTelemetry tracing configured: service=%s endpoint=%s", effective_name, _OTLP_ENDPOINT)
    except ImportError:
        logger.warning("opentelemetry packages not installed — tracing disabled for %s", effective_name)
    except Exception as exc:
        logger.warning("Tracing init failed for %s: %s", effective_name, exc)


def instrument_fastapi(app) -> None:
    """Attach OTLP FastAPI auto-instrumentation middleware.

    Call after configure_tracing() and after the FastAPI app is created.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation attached")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed — FastAPI tracing skipped")
    except Exception as exc:
        logger.warning("FastAPI OTEL instrumentation failed: %s", exc)
