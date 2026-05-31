"""Shared helpers for Databricks pipeline."""


def to_qdrant_point_id(point_id: int) -> int:
    """Plan: Qdrant point id = book_id / user_id (Gold schema uses int)."""
    return int(point_id)
