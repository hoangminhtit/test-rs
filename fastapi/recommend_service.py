"""Top-K recommendations — plan sections 11–12."""

from connect_qdrant import get_client
from config.qdrant_config import BOOK_COLLECTION, TOP_K, USER_COLLECTION
from utils import to_qdrant_point_id


def get_recommendations(user_id: int, top_k: int | None = None) -> dict:
    k = top_k or TOP_K
    client = get_client()

    user_points = client.retrieve(
        collection_name=USER_COLLECTION,
        ids=[to_qdrant_point_id(user_id)],
        with_vectors=True,
    )

    if not user_points or user_points[0].vector is None:
        return {"user_id": user_id, "recommendations": []}

    hits = sorted(
        client.search(
            collection_name=BOOK_COLLECTION,
            query_vector=user_points[0].vector,
            limit=k,
        ),
        key=lambda h: h.score,
        reverse=True,
    )

    return {
        "user_id": user_id,
        "recommendations": [
            {"book_id": int(hit.id), "score": round(hit.score, 4)} for hit in hits
        ],
    }
