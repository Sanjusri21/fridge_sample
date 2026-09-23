"""
Food Inventory Service.
Coordinates inventory management, enrichment, and gamification rewards upon consumption.
"""

from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.repository import FoodRepository, EventRepository
from app.food.expiry import enrich_food_item, calculate_days_remaining
from app.gamification.points import PointsService
from app.config.settings import logger


class FoodService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FoodRepository(db)
        self.event_repo = EventRepository(db)
        self.points_service = PointsService(db)

    def add_food(
        self,
        name: str,
        expiry_date: date,
        quantity: float = 1.0,
        unit: str = "pieces",
        category: str = "General",
        weight_grams: Optional[float] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        food = self.repo.add(
            name=name,
            expiry_date=expiry_date,
            quantity=quantity,
            unit=unit,
            category=category,
            weight_grams=weight_grams,
            image_path=image_path
        )
        self.event_repo.add("FOOD_ADDED", f"Added {food.name} ({quantity} {unit}) expiring on {food.expiry_date}")
        return enrich_food_item(food)

    def get_food(self, food_id: int) -> Optional[Dict[str, Any]]:
        food = self.repo.get_by_id(food_id)
        return enrich_food_item(food) if food else None

    def list_foods(self, status: Optional[str] = "active") -> List[Dict[str, Any]]:
        foods = self.repo.get_all(status=status)
        return [enrich_food_item(f) for f in foods]

    def update_food(self, food_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        food = self.repo.update(food_id, **kwargs)
        if food:
            self.event_repo.add("FOOD_UPDATED", f"Updated details for food item '{food.name}' (ID {food.id})")
            return enrich_food_item(food)
        return None

    def delete_food(self, food_id: int) -> bool:
        food = self.repo.get_by_id(food_id)
        if not food:
            return False
        name = food.name
        success = self.repo.delete(food_id)
        if success:
            self.event_repo.add("FOOD_DELETED", f"Removed food item '{name}' (ID {food_id})")
        return success

    def consume_food(self, food_id: int) -> Optional[Dict[str, Any]]:
        food = self.repo.get_by_id(food_id)
        if not food or food.status == "consumed":
            return None

        # Check if consumed before or on expiry
        days_left = calculate_days_remaining(food.expiry_date)
        was_before_expiry = days_left >= 0

        updated = self.repo.mark_consumed(food_id)
        if updated:
            if was_before_expiry:
                self.points_service.reward_consumed_before_expiry(food.name)
            else:
                self.points_service.penalize_expired_unused(food.name)

            self.event_repo.add("FOOD_CONSUMED", f"Consumed {food.name}. Expiry was {food.expiry_date}.")
            return enrich_food_item(updated)
        return None
