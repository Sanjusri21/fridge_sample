"""
Recipe Recommendation Engine for ALINA.
Suggests dishes focusing on ingredients nearest to expiry to minimize waste.
Includes sensible food-safety reminders without making medical claims.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.food.expiry import get_highest_priority_food
from app.ai.recipes import get_recipes_for_ingredient
from app.config.settings import logger


def recommend_recipe_for_fridge(db: Session) -> Dict[str, Any]:
    """
    Selects the food item closest to expiry, retrieves delicious recipes for it,
    and formats a helpful assistant recommendation.
    """
    highest_priority = get_highest_priority_food(db)

    if not highest_priority:
        return {
            "food_item": None,
            "recipes": [],
            "message": "Your fridge is currently empty. Add fresh groceries to receive personalized recipe ideas!"
        }

    food_name = highest_priority["name"]
    days = highest_priority["days_remaining"]
    recipes = get_recipes_for_ingredient(food_name)

    # Format time expression
    if days < 0:
        time_text = f"expired {abs(days)} day(s) ago"
    elif days == 0:
        time_text = "expires today"
    elif days == 1:
        time_text = "expires tomorrow"
    else:
        time_text = f"expires in {days} days"

    if recipes:
        chosen_recipe = recipes[0]
        alt_recipes = f" Other options include {', '.join(recipes[1:3])}." if len(recipes) > 1 else ""
        msg = (
            f"{food_name} {time_text}. I recommend {chosen_recipe} so you can use it before expiry.{alt_recipes} "
            f"Please check the product appearance and aroma before preparing."
        )
    else:
        msg = (
            f"{food_name} {time_text}. Consider incorporating it into today's meal to avoid waste. "
            f"Please verify product freshness before use."
        )

    logger.info("Generated recipe recommendation for %s (days left: %d)", food_name, days)
    return {
        "food_item": highest_priority,
        "recommended_recipe": recipes[0] if recipes else None,
        "all_recipes": recipes,
        "message": msg
    }
