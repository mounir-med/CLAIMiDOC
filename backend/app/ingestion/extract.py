from __future__ import annotations

from pathlib import Path

import pymupdf

from app.ingestion.ocr import ocr_image_bytes

MIN_NATIVE_CHARS = 40


def extract_pages(path: Path, ocr: bool = True) -> tuple[list[str], bool]:
    """Retourne (textes par page, ocr_utilise). PyMuPDF pour le texte natif, OCR si la page est une image."""
    pages: list[str] = []
    used_ocr = False
    with pymupdf.open(path) as doc:
        for page in doc:
            text = page.get_text("text")
            if len(text.strip()) < MIN_NATIVE_CHARS and ocr:
                png = page.get_pixmap(dpi=200).tobytes("png")
                text = ocr_image_bytes(png)
                used_ocr = True
            pages.append(text)
    return pages, used_ocr
