from __future__ import annotations

import hashlib
import re
import uuid

from pydantic import BaseModel

_NS = uuid.UUID("6f0f3f0e-6f58-4c3e-9a3a-0c1a1d0c1a11")


def content_hash(text: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode()).hexdigest()


class ChunkRecord(BaseModel):
    chunk_id: str
    doc_id: str
    version: str
    page: int
    article: str | None
    famille: str
    niveau_acces: str
    hash_contenu: str
    is_current: bool
    doc_type: str
    title: str
    text: str

    def payload(self) -> dict:
        return self.model_dump()


def make_chunk_id(doc_id: str, version: str, page: int, article: str | None, h: str) -> str:
    return str(uuid.uuid5(_NS, f"{doc_id}|{version}|{page}|{article}|{h}"))
