"""
Food Consumption Detection via Weight/Load Cell Changes.
Detects significant weight reductions, logs WEIGHT_CHANGED event,
and handles user confirmation before updating inventory and awarding points.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Food
from app.database.repository import EventRepository
from app.food.inventory import FoodService
from app.config.settings import logger


class ConsumptionService:
    def __init__(self, db: Session):
        self.db = db
        self.food_service = FoodService(db)
        self.event_repo = EventRepository(db)

    def detect_weight_change(
        self,
        previous_weight: float,
        current_weight: float,
        threshold_grams: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates delta between previous and current scale reading.
        If reduction exceeds threshold, finds potential candidate food item.
        """
        delta = previous_weight - current_weight
        if delta >= threshold_grams:
            self.event_repo.add(
                "WEIGHT_CHANGED",
                f"Scale weight decreased by {delta:.1f}g (from {previous_weight:.1f}g to {current_weight:.1f}g)"
            )

            # Find active food closest in weight or expiring soonest
            active_foods = self.food_service.list_foods(status="active")
            candidate = None
            if active_foods:
                # Find item whose weight_grams or quantity matches delta closely
                candidates_with_weight = [f for f in active_foods if f.get("weight_grams")]
                if candidates_with_weight:
                    # Pick closest weight match
                    candidate = min(candidates_with_weight, key=lambda f: abs((f["weight_grams"] or 0) - delta))
                else:
                    # Fallback to item expiring soonest
                    candidate = active_foods[0]

            return {
                "detected": True,
                "delta_grams": round(delta, 1),
                "candidate_food": candidate,
                "confirmation_prompt": (
                    f"Did you use the {candidate['name']}? ({delta:.0f}g reduction detected)"
                    if candidate else f"Weight decreased by {delta:.0f}g. Did you consume an item?"
                )
            }

        return None

    def confirm_consumption(
        self,
        food_id: int,
        confirmed: bool,
        consumed_weight_grams: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Processes user confirmation. If confirmed, marks item consumed or deducts weight,
        and awards gamification points.
        """
        if not confirmed:
            self.event_repo.add("CONSUMPTION_SKIPPED", f"User declined consumption confirmation for item id {food_id}")
            return {"status": "declined", "message": "Consumption cancelled by user."}

        food = self.food_service.get_food(food_id)
        if not food:
            return {"status": "error", "message": "Food item not found."}

        # If partial consumption is specified and weight remains
        if consumed_weight_grams and food.get("weight_grams") and food["weight_grams"] > consumed_weight_grams:
            new_weight = food["weight_grams"] - consumed_weight_grams
            self.food_service.update_food(food_id, weight_grams=new_weight)
            self.food_service.points_service.reward_consumed_before_expiry(food["name"])
            self.event_repo.add("FOOD_PARTIALLY_CONSUMED", f"Used {consumed_weight_grams:.0f}g of {food['name']}. Remaining: {new_weight:.0f}g")
            return {
                "status": "partial_success",
                "message": f"Updated {food['name']}. Remaining: {new_weight:.0f}g.",
                "item": self.food_service.get_food(food_id)
            }
        else:
            # Full consumption
            result = self.food_service.consume_food(food_id)
            return {
                "status": "success",
                "message": f"Marked {food['name']} as consumed! +10 points awarded.",
                "item": result
            }
