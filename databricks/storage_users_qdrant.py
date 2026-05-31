"""
Sync user embeddings to Qdrant (Pipeline 2: after create_user_embeddings).

Uses batched upsert via toLocalIterator() to avoid driver OOM on large user bases.
"""

from qdrant_client.models import PointStruct

from config.databricks_config import USER_EMBEDDINGS_TABLE, get_spark, output_table_path
from config.qdrant_config import USER_COLLECTION
from qdrant_common import ensure_collection, get_qdrant_client, upsert_rows_in_batches
from utils import to_qdrant_point_id


def _user_point(row) -> PointStruct:
    return PointStruct(
        id=to_qdrant_point_id(row.user_id),
        vector=row.embedding,
        payload={"user_id": int(row.user_id)},
    )


def sync_user_embeddings(client) -> int:
    spark = get_spark()
    df = spark.table(output_table_path(USER_EMBEDDINGS_TABLE))
    return upsert_rows_in_batches(
        client,
        USER_COLLECTION,
        df.toLocalIterator(),
        _user_point,
    )


def storage_users_qdrant() -> int:
    client = get_qdrant_client()
    ensure_collection(client, USER_COLLECTION)
    count = sync_user_embeddings(client)
    print(f"Synced {count} users")
    return count


if __name__ == "__main__":
    storage_users_qdrant()
