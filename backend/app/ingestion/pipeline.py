from __future__ import annotations

import json
from pathlib import Path

from app.ingestion.chunking import chunk_pages
from app.ingestion.extract import extract_pages
from app.ingestion.metadata import ChunkRecord, content_hash, make_chunk_id


def load_manifest(corpus: Path) -> list[dict]:
    return json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))


def build_records(corpus: Path, entry: dict, ocr: bool = True) -> list[ChunkRecord]:
    pages, _ = extract_pages(corpus / entry["file"], ocr=ocr)
    records = []
    for ch in chunk_pages(pages):
        h = content_hash(ch.text)
        records.append(
            ChunkRecord(
                chunk_id=make_chunk_id(entry["doc_id"], entry["version"], ch.page, ch.article, h),
                doc_id=entry["doc_id"], version=entry["version"], page=ch.page, article=ch.article,
                famille=entry["famille"], niveau_acces=entry["niveau_acces"], hash_contenu=h,
                is_current=entry["is_current"], doc_type=entry["doc_type"], title=entry["title"], text=ch.text,
            )
        )
    return records


def build_all_records(corpus: Path, ocr: bool = True) -> list[ChunkRecord]:
    out: list[ChunkRecord] = []
    for entry in load_manifest(corpus):
        out.extend(build_records(corpus, entry, ocr=ocr))
    return out
