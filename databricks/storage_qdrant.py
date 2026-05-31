"""
Upsert book and user embeddings from Delta tables into Qdrant collections.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config.databricks_config import (
    BOOK_EMBEDDINGS_TABLE,
    BOOKS_TABLE,
    USER_EMBEDDINGS_TABLE,
    get_spark,
    table_path,
)
from config.qdrant_config import (
    BOOK_COLLECTION,
    QDRANT_API_KEY,
    QDRANT_URL,
    USER_COLLECTION,
    VECTOR_SIZE,
)
from utils import to_qdrant_point_id


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)


def ensure_collections(client: QdrantClient):
    for name in (BOOK_COLLECTION, USER_COLLECTION):
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )


def sync_book_embeddings(client: QdrantClient) -> int:
    spark = get_spark()
    books_df = spark.table(table_path(BOOKS_TABLE))
    embeddings_df = spark.table(table_path(BOOK_EMBEDDINGS_TABLE))
    joined = embeddings_df.join(books_df, on="book_id", how="inner").collect()

    points = [
        PointStruct(
            id=to_qdrant_point_id(row.book_id),
            vector=row.embedding,
            payload={
                "book_id": row.book_id,
                "title": row.title,
                "category": row.category,
                "author": row.author,
            },
        )
        for row in joined
    ]

    if points:
        client.upsert(collection_name=BOOK_COLLECTION, points=points)
    return len(points)


def sync_user_embeddings(client: QdrantClient) -> int:
    spark = get_spark()
    users_df = spark.table(table_path(USER_EMBEDDINGS_TABLE)).collect()

    points = [
        PointStruct(
            id=to_qdrant_point_id(row.user_id),
            vector=row.embedding,
            payload={"user_id": row.user_id},
        )
        for row in users_df
    ]

    if points:
        client.upsert(collection_name=USER_COLLECTION, points=points)
    return len(points)


def storage_qdrant():
    client = get_qdrant_client()
    ensure_collections(client)
    book_count = sync_book_embeddings(client)
    user_count = sync_user_embeddings(client)
    return {"books": book_count, "users": user_count}


if __name__ == "__main__":
    result = storage_qdrant()
    print(f"Synced to Qdrant: {result}")
