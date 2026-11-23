"""Embeddings : BGE-M3 (dense + sparse lexical) en production, HashEmbedder déterministe pour tests/CI."""
from __future__ import annotations

import math
import re
import unicodedata
import zlib
from dataclasses import dataclass
from typing import Protocol

STOPWORDS = frozenset(
    "le la les un une des du de d l au aux et ou en est sont a à pour par sur dans que qui quoi quelle quel quelles quels "
    "ce cet cette ces se sa son ses leur leurs ne pas plus il elle on nous vous ils elles y the of and to is in".split()
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def tokens(text: str, drop_stop: bool = True) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", normalize(text))
    return [t for t in toks if not (drop_stop and (t in STOPWORDS or len(t) < 2))]


@dataclass
class Embedding:
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[Embedding]: ...


class HashEmbedder:
    """Déterministe, sans modèle : hashing trick. Réservé aux tests et au développement hors-ligne."""

    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[Embedding]:
        out = []
        for text in texts:
            toks = tokens(text)
            dense = [0.0] * self.dim
            tf: dict[int, float] = {}
            for t in toks:
                h = zlib.crc32(t.encode())
                dense[h % self.dim] += 1.0 if (h >> 16) & 1 else -1.0
                dense[(h * 31) % self.dim] += 0.5
                tf[h % (2**20)] = tf.get(h % (2**20), 0.0) + 1.0
            norm = math.sqrt(sum(v * v for v in dense)) or 1.0
            idx = sorted(tf)
            out.append(Embedding([v / norm for v in dense], idx, [1.0 + math.log(tf[i]) for i in idx]))
        return out


class BgeM3Embedder:
    """BAAI/bge-m3 via FlagEmbedding (dense 1024 + poids lexicaux creux). Nécessite l'extra `ml`."""

    dim = 1024

    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True):
        from FlagEmbedding import BGEM3FlagModel  # import tardif : dépendance lourde

        self.model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

    def embed(self, texts: list[str]) -> list[Embedding]:
        res = self.model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False, batch_size=16)
        out = []
        for dense, sparse in zip(res["dense_vecs"], res["lexical_weights"], strict=True):
            idx = [int(k) for k in sparse]
            out.append(Embedding([float(x) for x in dense], idx, [float(sparse[str(k)] if str(k) in sparse else sparse[k]) for k in idx]))
        return out


def make_embedder(name: str) -> Embedder:
    if name == "hash":
        return HashEmbedder()
    if name == "bge-m3":
        return BgeM3Embedder()
    raise ValueError(f"Embedder inconnu : {name}")
