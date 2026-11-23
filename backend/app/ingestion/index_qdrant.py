from __future__ import annotations

from qdrant_client import QdrantClient, models

from app.ingestion.embed import Embedder
from app.ingestion.metadata import ChunkRecord

DENSE, SPARSE = "dense", "lexical"


def ensure_collection(client: QdrantClient, name: str, dim: int, recreate: bool = False) -> None:
    exists = client.collection_exists(name)
    if exists and recreate:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            name,
            vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={SPARSE: models.SparseVectorParams()},
        )
    for field, schema in (("niveau_acces", "keyword"), ("famille", "keyword"), ("doc_id", "keyword"), ("is_current", "bool")):
        try:
            client.create_payload_index(name, field, field_schema=schema)
        except Exception:  # noqa: BLE001, S110 - le mode mémoire ignore les index ; déjà existant côté serveur
            pass


def upsert_chunks(client: QdrantClient, name: str, records: list[ChunkRecord], embedder: Embedder, batch: int = 32) -> int:
    n = 0
    for i in range(0, len(records), batch):
        part = records[i : i + batch]
        embs = embedder.embed([r.text for r in part])
        points = [
            models.PointStruct(
                id=r.chunk_id,
                vector={DENSE: e.dense, SPARSE: models.SparseVector(indices=e.sparse_indices, values=e.sparse_values)},
                payload=r.payload(),
            )
            for r, e in zip(part, embs, strict=True)
        ]
        client.upsert(name, points=points)
        n += len(points)
    return n
