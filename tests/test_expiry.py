"""
Unit tests for Expiry Calculation and Priority Engine.
"""

from datetime import date
from app.food.expiry import calculate_days_remaining, calculate_priority


def test_expiry_days_calculation():
    # As requested in prompt: Expiry: 2026-09-20, Today: 2026-09-19 -> 1 day
    today = date(2026, 9, 19)
    expiry = date(2026, 9, 20)
    days = calculate_days_remaining(expiry, reference_date=today)
    assert days == 1


def test_expiry_past_date():
    today = date(2026, 9, 19)
    expiry = date(2026, 9, 15)
    days = calculate_days_remaining(expiry, reference_date=today)
    assert days == -4


def test_priority_levels():
    # 0 or negative days -> EXPIRED
    assert calculate_priority(0) == "EXPIRED"
    assert calculate_priority(-3) == "EXPIRED"

    # 1 day -> CRITICAL
    assert calculate_priority(1) == "CRITICAL"

    # 2-3 days -> HIGH
    assert calculate_priority(2) == "HIGH"
    assert calculate_priority(3) == "HIGH"

    # 4-5 days -> MEDIUM
    assert calculate_priority(4) == "MEDIUM"
    assert calculate_priority(5) == "MEDIUM"

    # 6+ days -> NORMAL
    assert calculate_priority(6) == "NORMAL"
    assert calculate_priority(14) == "NORMAL"
