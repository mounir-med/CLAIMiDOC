"""CLI : python -m app.ingestion.run_ingestion --corpus ../data/corpus [--recreate]"""
from __future__ import annotations

import argparse
from pathlib import Path

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.ingestion.embed import make_embedder
from app.ingestion.index_qdrant import ensure_collection, upsert_chunks
from app.ingestion.pipeline import build_all_records


def main() -> None:
    s = get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=s.corpus_dir)
    ap.add_argument("--qdrant-url", default=s.qdrant_url)
    ap.add_argument("--collection", default=s.qdrant_collection)
    ap.add_argument("--embedder", default=s.embedder)
    ap.add_argument("--recreate", action="store_true")
    ap.add_argument("--no-ocr", action="store_true")
    a = ap.parse_args()
    embedder = make_embedder(a.embedder)
    client = QdrantClient(a.qdrant_url)
    ensure_collection(client, a.collection, embedder.dim, recreate=a.recreate)
    records = build_all_records(Path(a.corpus), ocr=not a.no_ocr)
    n = upsert_chunks(client, a.collection, records, embedder)
    print(f"{n} chunks indexés dans '{a.collection}' (embedder={a.embedder})")


if __name__ == "__main__":
    main()
