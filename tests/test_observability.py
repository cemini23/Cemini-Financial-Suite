"""
tests/test_observability.py — Pure unit tests for Step 35 observability stack.

All tests are PURE — no network, no Redis, no Postgres, no Docker daemon.
Run: PYTHONPATH=/opt/cemini pytest tests/test_observability.py -v

Coverage:
  35a — Prometheus config validity + FastAPI /metrics wiring
  35b — Loki config validity
  35c — Alloy config syntax validation
  35d — Tracing module (configure_tracing / instrument_fastapi)
  35e — Grafana datasource YAML structure + dashboard JSON validity
"""
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

REPO_ROOT = Path(__file__).parent.parent
MONITORING = REPO_ROOT / "monitoring"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ===========================================================================
# 35a — Prometheus config
# ===========================================================================


class TestPrometheusConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = load_yaml(MONITORING / "prometheus" / "prometheus.yml")

    def test_global_scrape_interval(self):
        """Global scrape_interval must be defined."""
        self.assertIn("scrape_interval", self.cfg.get("global", {}))

    def test_scrape_configs_present(self):
        """scrape_configs list must not be empty."""
        jobs = self.cfg.get("scrape_configs", [])
        self.assertGreater(len(jobs), 0)

    def test_required_scrape_targets(self):
        """All expected services appear as scrape jobs."""
        jobs = {j["job_name"] for j in self.cfg.get("scrape_configs", [])}
        required = {"kalshi_autopilot", "cemini_mcp", "redis", "postgres", "node"}
        self.assertTrue(required.issubset(jobs), f"Missing jobs: {required - jobs}")

    def test_kalshi_metrics_path(self):
        """kalshi_autopilot job uses /metrics path."""
        jobs = {j["job_name"]: j for j in self.cfg.get("scrape_configs", [])}
        kj = jobs.get("kalshi_autopilot", {})
        self.assertEqual(kj.get("metrics_path", "/metrics"), "/metrics")

    def test_static_configs_have_targets(self):
        """Every scrape job must list at least one target."""
        for job in self.cfg.get("scrape_configs", []):
            for sc in job.get("static_configs", []):
                self.assertGreater(len(sc.get("targets", [])), 0, f"Empty targets in {job['job_name']}")


# ===========================================================================
# 35a — FastAPI instrumentation wiring
# ===========================================================================


class TestPrometheusInstrumentatorWiring(unittest.TestCase):

    def test_metrics_endpoint_returns_200(self):
        """Prometheus instrumentator attaches /metrics and returns 200."""
        fastapi = pytest_import("fastapi")
        if fastapi is None:
            self.skipTest("fastapi not installed")
        instrumentator_mod = pytest_import("prometheus_fastapi_instrumentator")
        if instrumentator_mod is None:
            self.skipTest("prometheus_fastapi_instrumentator not installed")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from prometheus_fastapi_instrumentator import Instrumentator

        app = FastAPI()

        @app.get("/ping")
        def ping():
            return {"status": "ok"}

        Instrumentator().instrument(app).expose(app)
        client = TestClient(app)

        resp = client.get("/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("http_requests_total", resp.text)

    def test_quantos_create_app_has_metrics(self):
        """QuantOS create_app() includes /metrics route when deps present."""
        fastapi = pytest_import("fastapi")
        if fastapi is None:
            self.skipTest("fastapi not installed")
        instrumentator_mod = pytest_import("prometheus_fastapi_instrumentator")
        if instrumentator_mod is None:
            self.skipTest("prometheus_fastapi_instrumentator not installed")

        sys.path.insert(0, str(REPO_ROOT / "QuantOS"))
        try:
            # Mock heavy QuantOS imports that aren't available in test env
            _mock_module("interface.server", router=MagicMock())
            from interface import create_app
            from fastapi.testclient import TestClient
            app = create_app()
            routes = {r.path for r in app.routes}
            self.assertIn("/metrics", routes)
        finally:
            sys.path.pop(0)
            # Cleanup injected mock
            sys.modules.pop("interface.server", None)


# ===========================================================================
# 35b — Loki config
# ===========================================================================


class TestLokiConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = load_yaml(MONITORING / "loki" / "loki-config.yml")

    def test_auth_disabled(self):
        """Loki auth_enabled must be false for single-node setup."""
        self.assertFalse(self.cfg.get("auth_enabled", True))

    def test_http_port_present(self):
        """Loki http_listen_port must be 3100."""
        self.assertEqual(self.cfg["server"]["http_listen_port"], 3100)

    def test_retention_period(self):
        """Retention must be 720h (30 days)."""
        retention = self.cfg.get("limits_config", {}).get("retention_period", "")
        self.assertEqual(retention, "720h")

    def test_schema_config_present(self):
        """schema_config must have at least one entry."""
        schemas = self.cfg.get("schema_config", {}).get("configs", [])
        self.assertGreater(len(schemas), 0)

    def test_storage_filesystem(self):
        """Common storage backend must be filesystem."""
        storage = self.cfg.get("common", {}).get("storage", {})
        self.assertIn("filesystem", storage)


# ===========================================================================
# 35c — Alloy config syntax
# ===========================================================================


class TestAlloyConfig(unittest.TestCase):

    def setUp(self):
        self.alloy_path = MONITORING / "alloy" / "config.alloy"
        self.content = self.alloy_path.read_text()

    def test_file_exists(self):
        self.assertTrue(self.alloy_path.exists())

    def test_loki_write_endpoint_present(self):
        """Alloy config must reference Loki write endpoint."""
        self.assertIn("loki:3100", self.content)

    def test_tempo_export_present(self):
        """Alloy config must export traces to Tempo."""
        self.assertIn("tempo:4317", self.content)

    def test_docker_discovery_configured(self):
        """Alloy must use docker discovery for log collection."""
        self.assertIn("discovery.docker", self.content)

    def test_otlp_receiver_configured(self):
        """Alloy must have an OTLP receiver for traces."""
        self.assertIn("otelcol.receiver.otlp", self.content)

    def test_no_auth_credentials_hardcoded(self):
        """No plaintext passwords should appear in Alloy config."""
        lower = self.content.lower()
        for bad in ("password=", "secret=", "token="):
            self.assertNotIn(bad, lower)


# ===========================================================================
# 35d — Tempo config
# ===========================================================================


class TestTempoConfig(unittest.TestCase):

    def setUp(self):
        self.cfg = load_yaml(MONITORING / "tempo" / "tempo-config.yml")

    def test_http_port(self):
        """Tempo HTTP port must be 3200."""
        self.assertEqual(self.cfg["server"]["http_listen_port"], 3200)

    def test_otlp_grpc_receiver(self):
        """Tempo must have OTLP gRPC receiver on 4317."""
        grpc = (
            self.cfg.get("distributor", {})
            .get("receivers", {})
            .get("otlp", {})
            .get("protocols", {})
            .get("grpc", {})
        )
        self.assertIn("endpoint", grpc)
        self.assertIn("4317", grpc["endpoint"])

    def test_storage_wal_path(self):
        """Tempo WAL path must be configured."""
        wal_path = self.cfg["storage"]["trace"]["wal"]["path"]
        self.assertIn("tempo", wal_path)

    def test_local_storage_backend(self):
        """Tempo storage backend must be local."""
        backend = self.cfg["storage"]["trace"]["backend"]
        self.assertEqual(backend, "local")


# ===========================================================================
# 35d — Tracing module
# ===========================================================================


class TestTracingModule(unittest.TestCase):

    def test_configure_tracing_no_otel_installed(self):
        """configure_tracing must not raise when opentelemetry not installed."""
        # Temporarily hide opentelemetry from imports
        with patch.dict("sys.modules", {"opentelemetry": None, "opentelemetry.sdk": None}):
            from observability.tracing import configure_tracing
            # Should silently swallow ImportError
            try:
                configure_tracing("test-service")
            except Exception as exc:
                self.fail(f"configure_tracing raised with missing deps: {exc}")

    def test_configure_tracing_with_mock_otel(self):
        """configure_tracing calls set_tracer_provider when opentelemetry is available."""
        mock_trace = MagicMock()
        mock_provider = MagicMock()
        mock_exporter = MagicMock()
        mock_processor = MagicMock()
        mock_resource = MagicMock()

        fake_otel = types.ModuleType("opentelemetry")
        fake_otel.trace = mock_trace

        fake_sdk_trace = types.ModuleType("opentelemetry.sdk.trace")
        fake_sdk_trace.TracerProvider = MagicMock(return_value=mock_provider)

        fake_sdk_export = types.ModuleType("opentelemetry.sdk.trace.export")
        fake_sdk_export.BatchSpanProcessor = MagicMock(return_value=mock_processor)

        fake_sdk_resources = types.ModuleType("opentelemetry.sdk.resources")
        fake_sdk_resources.Resource = MagicMock()
        fake_sdk_resources.Resource.create = MagicMock(return_value=mock_resource)

        fake_exporter_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
        fake_exporter_mod.OTLPSpanExporter = MagicMock(return_value=mock_exporter)

        modules_patch = {
            "opentelemetry": fake_otel,
            "opentelemetry.trace": mock_trace,
            "opentelemetry.sdk": types.ModuleType("opentelemetry.sdk"),
            "opentelemetry.sdk.trace": fake_sdk_trace,
            "opentelemetry.sdk.trace.export": fake_sdk_export,
            "opentelemetry.sdk.resources": fake_sdk_resources,
            "opentelemetry.exporter": types.ModuleType("opentelemetry.exporter"),
            "opentelemetry.exporter.otlp": types.ModuleType("opentelemetry.exporter.otlp"),
            "opentelemetry.exporter.otlp.proto": types.ModuleType("opentelemetry.exporter.otlp.proto"),
            "opentelemetry.exporter.otlp.proto.grpc": types.ModuleType("opentelemetry.exporter.otlp.proto.grpc"),
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": fake_exporter_mod,
        }

        import importlib
        import observability.tracing as tracing_mod
        importlib.reload(tracing_mod)

        with patch.dict("sys.modules", modules_patch):
            importlib.reload(tracing_mod)
            tracing_mod.configure_tracing("cemini-test")
            mock_trace.set_tracer_provider.assert_called_once()

    def test_instrument_fastapi_no_otel(self):
        """instrument_fastapi must not raise when OTEL instrumentation not installed."""
        with patch.dict("sys.modules", {"opentelemetry.instrumentation.fastapi": None}):
            from observability.tracing import instrument_fastapi
            app_mock = MagicMock()
            try:
                instrument_fastapi(app_mock)
            except Exception as exc:
                self.fail(f"instrument_fastapi raised with missing deps: {exc}")

    def test_otlp_endpoint_env_override(self):
        """OTEL_EXPORTER_OTLP_ENDPOINT env var overrides default."""
        import importlib
        import os
        import observability.tracing as tracing_mod
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://custom-host:4317"}):
            importlib.reload(tracing_mod)
            self.assertEqual(tracing_mod._OTLP_ENDPOINT, "http://custom-host:4317")
        # Restore default
        importlib.reload(tracing_mod)


# ===========================================================================
# 35e — Grafana datasource provisioning
# ===========================================================================


class TestGrafanaDatasources(unittest.TestCase):

    def setUp(self):
        self.cfg = load_yaml(
            MONITORING / "grafana" / "provisioning" / "datasources" / "datasources.yml"
        )

    def test_api_version(self):
        self.assertEqual(self.cfg.get("apiVersion"), 1)

    def test_three_datasources(self):
        """Must provision Prometheus, Loki, and Tempo."""
        names = {ds["name"] for ds in self.cfg.get("datasources", [])}
        self.assertIn("Prometheus", names)
        self.assertIn("Loki", names)
        self.assertIn("Tempo", names)

    def test_prometheus_is_default(self):
        """Prometheus must be marked as default datasource."""
        ds_map = {ds["name"]: ds for ds in self.cfg.get("datasources", [])}
        self.assertTrue(ds_map["Prometheus"].get("isDefault"))

    def test_prometheus_url_correct(self):
        ds_map = {ds["name"]: ds for ds in self.cfg.get("datasources", [])}
        self.assertEqual(ds_map["Prometheus"]["url"], "http://prometheus:9090")

    def test_loki_url_correct(self):
        ds_map = {ds["name"]: ds for ds in self.cfg.get("datasources", [])}
        self.assertEqual(ds_map["Loki"]["url"], "http://loki:3100")

    def test_tempo_url_correct(self):
        ds_map = {ds["name"]: ds for ds in self.cfg.get("datasources", [])}
        self.assertEqual(ds_map["Tempo"]["url"], "http://tempo:3200")

    def test_tempo_trace_to_logs_correlation(self):
        """Tempo datasource must configure trace-to-logs correlation with Loki."""
        ds_map = {ds["name"]: ds for ds in self.cfg.get("datasources", [])}
        json_data = ds_map["Tempo"].get("jsonData", {})
        self.assertIn("tracesToLogs", json_data)
        self.assertEqual(json_data["tracesToLogs"]["datasourceUid"], "loki")


# ===========================================================================
# 35e — Dashboard JSON validity
# ===========================================================================


class TestGrafanaDashboards(unittest.TestCase):

    def _load_dashboard(self, filename: str) -> dict:
        return load_json(
            MONITORING / "grafana" / "provisioning" / "dashboards" / "cemini" / filename
        )

    def test_system_overview_valid_json(self):
        dash = self._load_dashboard("system-overview.json")
        self.assertIn("title", dash)
        self.assertIn("panels", dash)

    def test_system_overview_uid(self):
        dash = self._load_dashboard("system-overview.json")
        self.assertEqual(dash["uid"], "cemini-system-overview")

    def test_system_overview_has_panels(self):
        dash = self._load_dashboard("system-overview.json")
        self.assertGreater(len(dash["panels"]), 0)

    def test_trading_services_valid_json(self):
        dash = self._load_dashboard("trading-services.json")
        self.assertIn("title", dash)
        self.assertIn("panels", dash)

    def test_trading_services_uid(self):
        dash = self._load_dashboard("trading-services.json")
        self.assertEqual(dash["uid"], "cemini-trading-services")

    def test_trading_services_has_panels(self):
        dash = self._load_dashboard("trading-services.json")
        self.assertGreater(len(dash["panels"]), 0)

    def test_dashboard_schema_version(self):
        """Both dashboards must have a schemaVersion field."""
        for fname in ("system-overview.json", "trading-services.json"):
            dash = self._load_dashboard(fname)
            self.assertIn("schemaVersion", dash, f"Missing schemaVersion in {fname}")


# ===========================================================================
# Helpers
# ===========================================================================


def pytest_import(name: str):
    """Try to import a module; return None if unavailable."""
    try:
        import importlib
        return importlib.import_module(name)
    except ImportError:
        return None


def _mock_module(full_name: str, **attrs):
    """Inject a mock module into sys.modules so imports don't fail."""
    parts = full_name.split(".")
    for i in range(len(parts)):
        key = ".".join(parts[: i + 1])
        if key not in sys.modules:
            sys.modules[key] = types.ModuleType(key)
    for k, v in attrs.items():
        setattr(sys.modules[full_name], k, v)


if __name__ == "__main__":
    unittest.main()
