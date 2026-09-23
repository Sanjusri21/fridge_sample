"""
ALINA Dynamic Expiry Engine.
Calculates days remaining from current date and evaluates priority levels:
- <= 0 days: EXPIRED
- 1 day: CRITICAL
- 2-3 days: HIGH
- 4-5 days: MEDIUM
- 6+ days: NORMAL
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Food
from app.config.settings import logger


def calculate_days_remaining(expiry_date: date, reference_date: Optional[date] = None) -> int:
    """Calculates remaining days dynamically from reference date (today by default)."""
    if reference_date is None:
        reference_date = date.today()
    return (expiry_date - reference_date).days


def calculate_priority(days_remaining: int) -> str:
    """Returns priority level string based on days remaining."""
    if days_remaining <= 0:
        return "EXPIRED"
    elif days_remaining == 1:
        return "CRITICAL"
    elif 2 <= days_remaining <= 3:
        return "HIGH"
    elif 4 <= days_remaining <= 5:
        return "MEDIUM"
    else:
        return "NORMAL"


def enrich_food_item(food: Food, reference_date: Optional[date] = None) -> Dict[str, Any]:
    """Appends dynamic days_remaining and priority to food dictionary."""
    data = food.to_dict()
    days = calculate_days_remaining(food.expiry_date, reference_date)
    priority = calculate_priority(days)
    data["days_remaining"] = days
    data["priority"] = priority
    return data


def get_expired_foods(db: Session) -> List[Dict[str, Any]]:
    """Returns all active food items that have already expired."""
    today = date.today()
    foods = db.query(Food).filter(Food.status == "active", Food.expiry_date < today).order_by(Food.expiry_date.asc()).all()
    return [enrich_food_item(f, today) for f in foods]


def get_expiring_today(db: Session) -> List[Dict[str, Any]]:
    """Returns active food items expiring today."""
    today = date.today()
    foods = db.query(Food).filter(Food.status == "active", Food.expiry_date == today).all()
    return [enrich_food_item(f, today) for f in foods]


def get_expiring_soon(db: Session, max_days: int = 3) -> List[Dict[str, Any]]:
    """Returns active foods expiring within max_days (including today and expired)."""
    today = date.today()
    foods = db.query(Food).filter(Food.status == "active").order_by(Food.expiry_date.asc()).all()
    result = []
    for f in foods:
        days = calculate_days_remaining(f.expiry_date, today)
        if days <= max_days:
            result.append(enrich_food_item(f, today))
    return result


def get_highest_priority_food(db: Session) -> Optional[Dict[str, Any]]:
    """
    Returns the single active food item with the highest expiry urgency:
    Closest to expiry, prioritizing items expiring today or soonest.
    """
    today = date.today()
    foods = db.query(Food).filter(Food.status == "active").order_by(Food.expiry_date.asc()).all()
    if not foods:
        return None

    # Sort so that items with fewest days remaining are first
    enriched = [enrich_food_item(f, today) for f in foods]
    # Filter out already expired if any unexpired exist, or return closest
    active_unexpired = [f for f in enriched if f["days_remaining"] >= 0]
    if active_unexpired:
        return active_unexpired[0]
    return enriched[0]
