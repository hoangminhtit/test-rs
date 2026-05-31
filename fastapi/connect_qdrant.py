"""Create and return a Qdrant client instance."""

from qdrant_client import QdrantClient

from config.qdrant_config import QDRANT_API_KEY, QDRANT_URL

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
    return _client
