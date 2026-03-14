"""
ORJSON drop-in replacement for FastAPI JSON responses.

Usage:
    from shared.feature_engine.orjson_response import ORJSONResponse

    @app.get("/endpoint", response_class=ORJSONResponse)
    async def my_endpoint():
        return {"data": [...]}

Do NOT retrofit existing endpoints in this step — drop-in for future use.
"""
from __future__ import annotations

import orjson
from fastapi.responses import JSONResponse


class ORJSONResponse(JSONResponse):
    """FastAPI response class using orjson for 2-3x faster serialization."""

    media_type = "application/json"

    def render(self, content: object) -> bytes:
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
        )
