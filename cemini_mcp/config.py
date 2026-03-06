"""cemini_mcp — configuration.

All runtime parameters come from environment variables.
"""
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")
DB_NAME = os.getenv("POSTGRES_DB", "qdb")

MCP_PORT = int(os.getenv("MCP_PORT", "8002"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")

# Staleness threshold: signal is "stale" if older than this many seconds
STALE_THRESHOLD_SEC = int(os.getenv("STALE_THRESHOLD_SEC", "600"))
