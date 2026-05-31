"""Shared helpers for FastAPI service."""

import hashlib
import uuid


def to_qdrant_point_id(raw_id) -> str:
    if isinstance(raw_id, int):
        return str(uuid.UUID(int=raw_id & ((1 << 128) - 1)))
    text = str(raw_id)
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return str(uuid.UUID(digest))
