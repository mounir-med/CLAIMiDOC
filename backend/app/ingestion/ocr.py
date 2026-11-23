from __future__ import annotations

import io
import os


class OcrUnavailable(RuntimeError):
    pass


def ocr_image_bytes(png: bytes, lang: str | None = None) -> str:
    """OCR local Tesseract (défaut). PaddleOCR peut être branché ici (OCR_ENGINE=paddle)."""
    lang = lang or os.environ.get("OCR_LANG", "fra+eng")
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise OcrUnavailable("pytesseract/Pillow non installés") from exc
    img = Image.open(io.BytesIO(png))
    try:
        return pytesseract.image_to_string(img, lang=lang)
    except pytesseract.TesseractError:
        # langue absente : repli sur l'anglais (documenté dans HYPOTHESES.md)
        return pytesseract.image_to_string(img, lang="eng")
