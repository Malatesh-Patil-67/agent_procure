from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models


COLLECTION = "supplier_evidence"
VECTOR_SIZE = 64


def _vector(text: str) -> list[float]:
    digest = hashlib.shake_256(text.encode()).digest(VECTOR_SIZE)
    return [byte / 255 for byte in digest]


def get_client() -> QdrantClient:
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


def index_documents(raw_directory: Path) -> int:
    client = get_client()
    client.recreate_collection(COLLECTION, vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE))
    points = []
    for path in raw_directory.rglob("*.pdf"):
        from .extraction import _read_document

        content = _read_document(path)
        points.append(models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, str(path))),
            vector=_vector(content),
            payload={"supplier_id": path.name.split("_")[0], "document": path.name, "page": 1, "passage": content},
        ))
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def search_evidence(query: str, limit: int = 5) -> list[dict]:
    client = get_client()
    results = client.query_points(collection_name=COLLECTION, query=_vector(query), limit=limit).points
    return [point.payload | {"similarity": point.score} for point in results]
