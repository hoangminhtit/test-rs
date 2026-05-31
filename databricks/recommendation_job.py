"""
Databricks workflows — two pipelines (can run as separate Jobs).

Pipeline 1 (books):
  create_book_embeddings → storage_books_qdrant

Pipeline 2 (users):
  create_user_weight_matrix → create_user_embeddings → storage_users_qdrant

Full run: both pipelines in sequence.
"""

from create_book_embeddings import create_book_embeddings
from create_user_embeddings import create_user_embeddings
from create_user_weight_matrix import create_user_weight_matrix
from storage_books_qdrant import storage_books_qdrant
from storage_users_qdrant import storage_users_qdrant


def run_books_pipeline() -> dict:
    print("Pipeline 1: create_book_embeddings")
    book_count = create_book_embeddings()
    print(f"  → {book_count} book embeddings")

    print("Pipeline 1: storage_books_qdrant")
    qdrant_books = storage_books_qdrant()
    print(f"  → {qdrant_books} books in Qdrant")

    return {"book_embeddings": book_count, "qdrant_books": qdrant_books}


def run_users_pipeline() -> dict:
    print("Pipeline 2: create_user_weight_matrix")
    weight_count = create_user_weight_matrix()
    print(f"  → {weight_count} user-book weights")

    print("Pipeline 2: create_user_embeddings")
    user_count = create_user_embeddings()
    print(f"  → {user_count} user embeddings")

    print("Pipeline 2: storage_users_qdrant")
    qdrant_users = storage_users_qdrant()
    print(f"  → {qdrant_users} users in Qdrant")

    return {
        "user_book_weights": weight_count,
        "user_embeddings": user_count,
        "qdrant_users": qdrant_users,
    }


def run_recommendation_pipeline() -> dict:
    """Run both pipelines (full refresh)."""
    books = run_books_pipeline()
    users = run_users_pipeline()
    return {**books, **users}


if __name__ == "__main__":
    print("Pipeline completed:", run_recommendation_pipeline())
