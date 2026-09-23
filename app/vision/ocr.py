"""
OCR Engine with OpenCV image preprocessing.
Supports pytesseract OCR with automatic fallback if Tesseract binary is not installed.
Never fabricates detection results.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import numpy as np

from app.config.settings import settings, logger
from app.vision.expiry_parser import parse_expiry_date
from app.food.food_detection import identify_food_from_text

# Optional pytesseract import
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def check_tesseract_installed() -> Dict[str, Any]:
    """Checks if Tesseract executable is present and usable."""
    if not PYTESSERACT_AVAILABLE:
        return {
            "available": False,
            "reason": "pytesseract Python package is not installed.",
            "guide": "Run: pip install pytesseract"
        }

    # If user specified path in settings or standard windows paths
    candidates = [
        settings.TESSERACT_PATH,
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        shutil.which("tesseract")
    ]

    for path in candidates:
        if path and os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return {
                "available": True,
                "path": path,
                "reason": "Tesseract OCR engine is installed and ready."
            }

    return {
        "available": False,
        "reason": "Tesseract-OCR executable not found on Windows system.",
        "guide": (
            "To enable automated OCR on Windows:\n"
            "1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. Install to C:\\Program Files\\Tesseract-OCR\\\n"
            "3. Restart ALINA. Manual food and expiry entry remains fully functional."
        )
    }


def preprocess_image(image_input) -> Optional[np.ndarray]:
    """
    Applies OpenCV preprocessing pipeline:
    Grayscale -> Bilateral Filter (noise reduction preserving edges) -> Adaptive Thresholding / Otsu.
    """
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input))
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        return None

    if img is None:
        return None

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)

    # Adaptive Otsu thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh


def run_ocr(image_input) -> Dict[str, Any]:
    """
    Executes OCR on an image file or numpy frame.
    Returns:
    - ocr_available: bool
    - raw_text: str
    - detected_food: Optional[str]
    - detected_expiry: Optional[str] (YYYY-MM-DD)
    - status_message: str
    """
    tess_status = check_tesseract_installed()
    if not tess_status["available"]:
        logger.warning("OCR requested but Tesseract is unavailable: %s", tess_status["reason"])
        return {
            "ocr_available": False,
            "raw_text": "",
            "detected_food": None,
            "detected_category": "General",
            "detected_expiry": None,
            "status_message": (
                "Tesseract OCR is not installed. You can manually enter the food name and expiry date."
            ),
            "installation_guide": tess_status.get("guide", "")
        }

    try:
        processed = preprocess_image(image_input)
        if processed is None:
            return {
                "ocr_available": True,
                "raw_text": "",
                "detected_food": None,
                "detected_category": "General",
                "detected_expiry": None,
                "status_message": "Could not read or process the provided image.",
            }

        # Run OCR with pytesseract
        text = pytesseract.image_to_string(processed, config="--psm 6")
        logger.info("OCR raw extracted text: '%s'", text.strip().replace("\n", " "))

        # 1. Parse food identity
        food_match = identify_food_from_text(text)

        # 2. Parse expiry date
        expiry_date = parse_expiry_date(text)

        status_notes = []
        if food_match["identified"]:
            status_notes.append(f"Identified food: {food_match['name']}")
        else:
            status_notes.append("Food name not recognized automatically (please specify).")

        if expiry_date:
            status_notes.append(f"Detected expiry: {expiry_date.isoformat()}")
        else:
            status_notes.append("Expiry date not found in text (please enter manually).")

        return {
            "ocr_available": True,
            "raw_text": text.strip(),
            "detected_food": food_match["name"] if food_match["identified"] else None,
            "detected_category": food_match.get("category", "General"),
            "default_unit": food_match.get("default_unit", "pieces"),
            "default_qty": food_match.get("default_qty", 1.0),
            "detected_expiry": expiry_date.isoformat() if expiry_date else None,
            "status_message": " | ".join(status_notes),
        }

    except Exception as e:
        logger.error("Error executing OCR: %s", e)
        return {
            "ocr_available": True,
            "raw_text": "",
            "detected_food": None,
            "detected_category": "General",
            "detected_expiry": None,
            "status_message": f"OCR processing encountered an issue: {str(e)}. Please enter details manually.",
        }
