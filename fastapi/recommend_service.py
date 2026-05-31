"""Generate Top-K book recommendations for a user via Qdrant vector search."""

from connect_qdrant import get_client
from config.qdrant_config import BOOK_COLLECTION, TOP_K, USER_COLLECTION
from utils import to_qdrant_point_id


def get_recommendations(user_id: str, top_k: int | None = None) -> dict:
    """
    1. Load user vector from user_embeddings collection.
    2. Search book_embeddings by cosine similarity.
    3. Return Top-K books sorted by score.
    """
    k = top_k or TOP_K
    client = get_client()
    point_id = to_qdrant_point_id(user_id)

    user_points = client.retrieve(
        collection_name=USER_COLLECTION,
        ids=[point_id],
        with_vectors=True,
    )

    if not user_points or user_points[0].vector is None:
        return {
            "user_id": user_id,
            "recommendations": [],
            "message": "User embedding not found",
        }

    user_vector = user_points[0].vector

    search_results = client.search(
        collection_name=BOOK_COLLECTION,
        query_vector=user_vector,
        limit=k,
    )

    recommendations = [
        {
            "book_id": hit.payload.get("book_id", hit.id),
            "score": round(hit.score, 4),
            "title": hit.payload.get("title"),
            "author": hit.payload.get("author"),
            "category": hit.payload.get("category"),
        }
        for hit in sorted(search_results, key=lambda x: x.score, reverse=True)
    ]

    return {"user_id": user_id, "recommendations": recommendations}
