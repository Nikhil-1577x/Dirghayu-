"""
ocr_pipeline.py – Stub for OCR-based biomarker extraction.

In production, replace this with a real OCR pipeline (e.g., Tesseract, Google Vision API,
or a fine-tuned YOLO/DocTR model).

Expected return format:
  list of {"type": str, "value": float, "timestamp": str (ISO)}
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_ocr(image_path: str) -> list[dict]:
    """
    Run OCR on a lab report image and extract biomarker readings.

    Args:
        image_path: Absolute path to the image file.

    Returns:
        List of dicts: [{"type": "blood_glucose", "value": 95.5, "timestamp": "ISO"}, ...]
    """
    logger.info("OCR pipeline invoked for image: %s", image_path)

    # ── STUB implementation ─────────────────────────────────────────────────
    # Replace with actual OCR logic. Example:
    #   from PIL import Image
    #   import pytesseract
    #   img = Image.open(image_path)
    #   text = pytesseract.image_to_string(img)
    #   return parse_biomarkers(text)

    from app.utils.time_utils import utcnow_str

    # Return synthetic data so the system runs end-to-end in development
    return [
        {"type": "blood_glucose",    "value": 97.5,  "timestamp": utcnow_str()},
        {"type": "blood_pressure",   "value": 120.0, "timestamp": utcnow_str()},
        {"type": "oxygen_saturation","value": 98.0,  "timestamp": utcnow_str()},
    ]
