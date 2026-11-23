"""Découpage par article ET par page. Un article qui chevauche deux pages produit un chunk par page."""
from __future__ import annotations

import re
from dataclasses import dataclass

ARTICLE_RE = re.compile(r"^\s*Article\s+(\d+(?:\.\d+)*)\b", re.IGNORECASE | re.MULTILINE)
FOOTER_MARKER = "DOCUMENT SYNTHÉTIQUE"


@dataclass(frozen=True)
class RawChunk:
    page: int
    article: str | None
    text: str


def _clean(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines() if FOOTER_MARKER.lower() not in ln.lower()]
    return "\n".join(lines).strip()


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts, cur = [], ""
    for para in re.split(r"(?<=[.;])\s+", text):
        if cur and len(cur) + len(para) + 1 > max_chars:
            parts.append(cur)
            cur = para
        else:
            cur = f"{cur} {para}".strip()
    if cur:
        parts.append(cur)
    return parts


def chunk_pages(pages: list[str], max_chars: int = 1200) -> list[RawChunk]:
    """pages[i] = texte de la page i+1. Retourne des chunks (page, article, texte)."""
    chunks: list[RawChunk] = []
    current_article: str | None = None
    for i, raw in enumerate(pages, start=1):
        text = _clean(raw)
        if not text:
            continue
        matches = list(ARTICLE_RE.finditer(text))
        if not matches:
            segments = [(current_article, text)]
        else:
            segments = []
            head = text[: matches[0].start()].strip()
            if head:
                segments.append((current_article, head))
            for j, m in enumerate(matches):
                end = matches[j + 1].start() if j + 1 < len(matches) else len(text)
                current_article = m.group(1)
                segments.append((current_article, text[m.start():end].strip()))
        for article, seg in segments:
            for part in _split_long(seg, max_chars):
                if part.strip():
                    chunks.append(RawChunk(page=i, article=article, text=part))
    return chunks
