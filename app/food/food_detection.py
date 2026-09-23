"""
Food Identification Module.
Extracts recognized food items from OCR/transcription text using a known food dictionary.
Fails transparently without hallucinating if no match is found.
"""

import re
from typing import Optional, Dict, Any
from app.config.settings import logger

# Recognized pantry / fridge foods and their standardized metadata
FOOD_DICTIONARY = {
    "chicken": {"name": "Chicken", "category": "Meat", "default_unit": "grams", "default_qty": 500},
    "milk": {"name": "Milk", "category": "Dairy", "default_unit": "litre", "default_qty": 1},
    "egg": {"name": "Eggs", "category": "Poultry", "default_unit": "pieces", "default_qty": 6},
    "eggs": {"name": "Eggs", "category": "Poultry", "default_unit": "pieces", "default_qty": 6},
    "cheese": {"name": "Cheese", "category": "Dairy", "default_unit": "grams", "default_qty": 200},
    "apple": {"name": "Apple", "category": "Fruits", "default_unit": "pieces", "default_qty": 4},
    "apples": {"name": "Apple", "category": "Fruits", "default_unit": "pieces", "default_qty": 4},
    "bread": {"name": "Bread", "category": "Bakery", "default_unit": "slices", "default_qty": 10},
    "rice": {"name": "Rice", "category": "Grains", "default_unit": "grams", "default_qty": 500},
    "curd": {"name": "Curd", "category": "Dairy", "default_unit": "grams", "default_qty": 400},
    "yogurt": {"name": "Yogurt", "category": "Dairy", "default_unit": "grams", "default_qty": 200},
    "vegetable": {"name": "Vegetables", "category": "Produce", "default_unit": "grams", "default_qty": 500},
    "vegetables": {"name": "Vegetables", "category": "Produce", "default_unit": "grams", "default_qty": 500},
    "fish": {"name": "Fish", "category": "Seafood", "default_unit": "grams", "default_qty": 400},
}


def identify_food_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Scans raw text (from OCR or voice transcript) against the recognized food dictionary.
    Returns identification outcome with matched item or clear fallback prompt.
    """
    if not raw_text or not raw_text.strip():
        return {
            "identified": False,
            "name": None,
            "category": "General",
            "default_unit": "pieces",
            "default_qty": 1.0,
            "message": "No text detected to identify food.",
        }

    cleaned = re.sub(r"[^a-zA-Z\s]", " ", raw_text.lower())
    tokens = set(cleaned.split())

    # Exact token match first
    for token, meta in FOOD_DICTIONARY.items():
        if token in tokens:
            logger.info("Food identified from token match '%s' -> %s", token, meta["name"])
            return {
                "identified": True,
                "name": meta["name"],
                "category": meta["category"],
                "default_unit": meta["default_unit"],
                "default_qty": meta["default_qty"],
                "message": f"Identified as {meta['name']}.",
            }

    # Substring search if token exact match didn't catch (e.g. 'freshmilk')
    for key, meta in FOOD_DICTIONARY.items():
        if key in cleaned:
            logger.info("Food identified from substring '%s' -> %s", key, meta["name"])
            return {
                "identified": True,
                "name": meta["name"],
                "category": meta["category"],
                "default_unit": meta["default_unit"],
                "default_qty": meta["default_qty"],
                "message": f"Identified as {meta['name']}.",
            }

    # Honest fallback per user requirement:
    # "I could not identify the food. Please tell me the food name."
    logger.info("Could not identify food item from text: '%s'", raw_text[:50])
    return {
        "identified": False,
        "name": None,
        "category": "General",
        "default_unit": "pieces",
        "default_qty": 1.0,
        "message": "I could not identify the food. Please tell me the food name.",
    }
