# D11: Single source of truth for the Cemini Financial Suite version.
# Import from this module anywhere a version string is needed programmatically.
__version__ = "1.0.0"

# Per-service versions are preserved here for reference; the top-level
# __version__ is what external evaluators (buyers, CI, API health endpoints) see.
SERVICE_VERSIONS = {
    "quantos": "13.1.0",
    "ems": "1.0.0",
    "cemini_mcp": "1.0.0",
    "cemini_contracts": "1.0.0",
    "logit_pricing": "1.0.0",
    "opportunity_screener": "1.0.0",
    "kalshi_suite": "2.0.8",
}
