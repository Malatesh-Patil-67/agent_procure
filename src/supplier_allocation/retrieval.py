from __future__ import annotations

import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models
from ollama import Client


COLLECTION = "supplier_evidence"
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def _vector(text: str) -> list[float]:
    response = Client(host=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).embed(
        model=EMBEDDING_MODEL, input=text
    )
    return response["embeddings"][0]


def get_client() -> QdrantClient:
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


def index_documents(raw_directory: Path) -> int:
    client = get_client()
    points = []
    for path in raw_directory.rglob("*.pdf"):
        from .extraction import _read_document

        content = _read_document(path)
        points.append(models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, str(path))),
            vector=_vector(content),
            payload={"supplier_id": path.name.split("_")[0], "document": path.name, "page": 1, "passage": content},
        ))
    client.recreate_collection(
        COLLECTION,
        vectors_config=models.VectorParams(size=len(points[0].vector), distance=models.Distance.COSINE),
    )
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def search_evidence(query: str, limit: int = 5) -> list[dict]:
    client = get_client()
    try:
        results = client.query_points(collection_name=COLLECTION, query=_vector(query), limit=limit).points
    except Exception:
        return []
    return [point.payload | {"similarity": point.score} for point in results]
