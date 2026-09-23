"""
Unit tests for Expiry Date Parser and Food Identification.
"""

from datetime import date
from app.vision.expiry_parser import parse_expiry_date
from app.food.food_detection import identify_food_from_text


def test_date_parser_formats():
    expected = date(2026, 9, 14)

    # All requested test formats:
    samples = [
        "EXP 14/09/2026",
        "EXP: 14-09-2026",
        "Expiry: 14/09/26",
        "Best Before: 14/09/2026",
        "BB 14/09/2026",
        "2026-09-14",
        "14.09.2026",
        "14/09/2026",
        "14-09-2026",
    ]

    for sample in samples:
        parsed = parse_expiry_date(sample)
        assert parsed == expected, f"Failed parsing sample: {sample}, got: {parsed}"


def test_food_identification_positive():
    res1 = identify_food_from_text("Organic Whole Milk 1 Gallon")
    assert res1["identified"] is True
    assert res1["name"] == "Milk"

    res2 = identify_food_from_text("Fresh Chicken Breast 500g")
    assert res2["identified"] is True
    assert res2["name"] == "Chicken"

    res3 = identify_food_from_text("Grade A Eggs 12 Pack")
    assert res3["identified"] is True
    assert res3["name"] == "Eggs"


def test_food_identification_fallback():
    # Prompt rule: Do not pretend CV recognized an item when it did not
    res = identify_food_from_text("Unlabeled random plastic bottle 98412")
    assert res["identified"] is False
    assert res["name"] is None
    assert "I could not identify the food" in res["message"]
