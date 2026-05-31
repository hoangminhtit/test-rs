"""Qdrant connection settings for Databricks jobs."""

import os

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
BOOK_COLLECTION = os.getenv("BOOK_COLLECTION", "book_embeddings")
USER_COLLECTION = os.getenv("USER_COLLECTION", "user_embeddings")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "384"))
