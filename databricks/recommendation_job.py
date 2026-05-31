"""
Master Databricks workflow — runs the full recommendation pipeline in order.
Schedule: every 1 hour (configure in Databricks Jobs UI).
"""

from create_book_embeddings import create_book_embeddings
from create_user_embeddings import create_user_embeddings
from create_user_weight_matrix import create_user_weight_matrix
from storage_qdrant import storage_qdrant


def run_recommendation_pipeline():
    """Step 1 → 2 → 3 → 4 as defined in the project plan."""
    print("Step 1: create_book_embeddings")
    book_count = create_book_embeddings()
    print(f"  → {book_count} book embeddings")

    print("Step 2: create_user_weight_matrix")
    weight_count = create_user_weight_matrix()
    print(f"  → {weight_count} user-book weights")

    print("Step 3: create_user_embeddings")
    user_count = create_user_embeddings()
    print(f"  → {user_count} user embeddings")

    print("Step 4: storage_qdrant")
    sync_result = storage_qdrant()
    print(f"  → synced: {sync_result}")

    return {
        "book_embeddings": book_count,
        "user_book_weights": weight_count,
        "user_embeddings": user_count,
        "qdrant_sync": sync_result,
    }


if __name__ == "__main__":
    summary = run_recommendation_pipeline()
    print("Pipeline completed:", summary)
