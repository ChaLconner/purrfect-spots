import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from utils.telemetry import get_tracer, setup_telemetry


@pytest.fixture
def mock_app():
    return FastAPI()


def test_setup_telemetry_disabled(mock_app):
    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "false"}), patch("utils.telemetry.logger") as mock_logger:
        setup_telemetry(mock_app)
        # Should log that it's disabled
        mock_logger.info.assert_called_with("Telemetry disabled (ENABLE_TELEMETRY!=true)")


def test_setup_telemetry_enabled_import_error(mock_app):
    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        # We need to ensure the import fails
        # Using a side_effect on __import__ is tricky because it affects all imports
        # A safer way is to mock sys.modules to return nothing or raise error

        # If we remove it from sys.modules and make sure it cannot be found?
        # Alternatively, we can patch the function setup_telemetry logic or the import statement?
        # But we can't easily patch statements.

        # Let's try mocking the module to be None (which causes ModuleNotFoundError usually)
        with patch.dict(sys.modules, {"opentelemetry": None}):
            # We also need to patch __import__ strictly to raise ImportError if name starts with opentelemetry

            original_import = __import__

            def mock_import(name, *args, **kwargs):
                if name.startswith("opentelemetry"):
                    raise ImportError("No module named " + name)
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                with patch("utils.telemetry.logger") as mock_logger:
                    setup_telemetry(mock_app)
                    mock_logger.warning.assert_called_with(
                        "OpenTelemetry packages not found. Skipping telemetry setup."
                    )


def test_setup_telemetry_enabled_success(mock_app):
    with patch.dict(os.environ, {"ENABLE_TELEMETRY": "true"}):
        # Create mock modules and classes
        mock_trace = MagicMock()
        mock_resource = MagicMock()
        mock_instrumentor = MagicMock()

        # Configure mocks
        mock_resource_cls = MagicMock()
        mock_resource_cls.create.return_value = mock_resource

        mock_provider_instance = MagicMock()
        mock_provider_cls = MagicMock(return_value=mock_provider_instance)

        # Setup sys.modules
        mock_modules = {
            "opentelemetry": MagicMock(),
            "opentelemetry.trace": mock_trace,
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": MagicMock(OTLPSpanExporter=MagicMock()),
            "opentelemetry.instrumentation.fastapi": MagicMock(FastAPIInstrumentor=mock_instrumentor),
            "opentelemetry.sdk.resources": MagicMock(Resource=mock_resource_cls),
            "opentelemetry.sdk.trace": MagicMock(TracerProvider=mock_provider_cls),
            "opentelemetry.sdk.trace.export": MagicMock(BatchSpanProcessor=MagicMock()),
        }

        with patch.dict(sys.modules, mock_modules):
            setup_telemetry(mock_app)


def test_get_tracer_success():
    # If opentelemetry is installed, this returns a real tracer
    tracer = get_tracer("test")
    assert tracer is not None


def test_get_tracer_import_error():
    # Simulate ImportError
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("opentelemetry"):
            raise ImportError("No module named " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        tracer = get_tracer("test")
        # Should return DummyTracer
        assert hasattr(tracer, "start_as_current_span")
        with tracer.start_as_current_span("foo") as span:
            assert span is not None
