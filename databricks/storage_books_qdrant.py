"""
Sync book embeddings to Qdrant (Pipeline 1: after create_book_embeddings).

Uses batched upsert via toLocalIterator() to avoid driver OOM on large catalogs.
"""

from qdrant_client.models import PointStruct

from config.databricks_config import (
    BOOK_EMBEDDINGS_TABLE,
    DIM_BOOKS_TABLE,
    get_spark,
    gold_table_path,
    output_table_path,
)
from config.qdrant_config import BOOK_COLLECTION
from qdrant_common import ensure_collection, get_qdrant_client, upsert_rows_in_batches
from utils import to_qdrant_point_id


def _book_point(row) -> PointStruct:
    return PointStruct(
        id=to_qdrant_point_id(row.book_id),
        vector=row.embedding,
        payload={
            "book_id": int(row.book_id),
            "title": row.title,
            "category": row.category_name,
            "author": row.author,
        },
    )


def sync_book_embeddings(client) -> int:
    spark = get_spark()
    df = spark.table(output_table_path(BOOK_EMBEDDINGS_TABLE)).join(
        spark.table(gold_table_path(DIM_BOOKS_TABLE)),
        on="book_id",
        how="inner",
    )
    return upsert_rows_in_batches(
        client,
        BOOK_COLLECTION,
        df.toLocalIterator(),
        _book_point,
    )


def storage_books_qdrant() -> int:
    client = get_qdrant_client()
    ensure_collection(client, BOOK_COLLECTION)
    count = sync_book_embeddings(client)
    print(f"Synced {count} books")
    return count


if __name__ == "__main__":
    storage_books_qdrant()
