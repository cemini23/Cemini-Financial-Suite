"""Backward-compatibility helpers for gradual Pydantic migration.

Use safe_validate() at READ boundaries and safe_dump() at WRITE boundaries.
Neither function ever raises — existing behaviour is always preserved.
"""

import json
import logging
from typing import Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def safe_validate(model_class: Type[T], data) -> T | None:
    """Validate *data* against *model_class*, returning None on failure.

    Accepts dict, JSON str, or bytes.  Logs a warning on validation error
    but never crashes the caller — existing behaviour is preserved.
    """
    try:
        if isinstance(data, (str, bytes)):
            data = json.loads(data)
        return model_class.model_validate(data)
    except Exception as exc:
        logger.warning(
            "Contract validation failed for %s: %s (data keys: %s)",
            model_class.__name__,
            str(exc)[:200],
            list(data.keys()) if isinstance(data, dict) else "non-dict",
        )
        return None


def safe_dump(instance: BaseModel) -> str:
    """Serialize *instance* to a JSON string for Redis publish.

    Falls back to json.dumps on failure.
    """
    try:
        return instance.model_dump_json()
    except Exception as exc:
        logger.warning(
            "Contract serialization failed for %s: %s",
            type(instance).__name__,
            str(exc)[:200],
        )
        return json.dumps(instance.model_dump(), default=str)
