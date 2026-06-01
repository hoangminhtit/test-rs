"""Shared Qdrant client helpers and batched upsert (avoids driver OOM from .collect())."""

from collections.abc import Callable, Iterator
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config.qdrant_config import QDRANT_API_KEY, QDRANT_BATCH_SIZE, QDRANT_URL, VECTOR_SIZE


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=QDRANT_URL, 
        api_key=QDRANT_API_KEY,
        prefer_grpc=False
    )


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert_rows_in_batches(
    client: QdrantClient,
    collection_name: str,
    rows: Iterator[Any],
    to_point: Callable[[Any], PointStruct],
    batch_size: int | None = None,
) -> int:
    """Stream rows from Spark toLocalIterator() and upsert in fixed-size batches."""
    size = batch_size or QDRANT_BATCH_SIZE
    batch: list[PointStruct] = []
    total = 0

    for row in rows:
        batch.append(to_point(row))
        if len(batch) >= size:
            client.upsert(collection_name=collection_name, points=batch)
            total += len(batch)
            batch.clear()

    if batch:
        client.upsert(collection_name=collection_name, points=batch)
        total += len(batch)

    return total
