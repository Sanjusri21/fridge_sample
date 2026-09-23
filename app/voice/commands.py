"""
Modular Voice & Natural Language Command Router for ALINA.
Uses command intent handlers with regex/keyword matching instead of a single giant if/else chain.
"""

import re
from typing import Dict, Any, Callable, List, Optional
from sqlalchemy.orm import Session

from app.food.inventory import FoodService
from app.food.expiry import get_expiring_soon, get_expiring_today, get_expired_foods, get_highest_priority_food
from app.ai.recipes import get_recipes_for_ingredient
from app.ai.recommendations import recommend_recipe_for_fridge
from app.gamification.points import PointsService
from app.config.settings import logger


class VoiceCommandRouter:
    def __init__(self, db: Session, sensor_manager=None):
        self.db = db
        self.sensor_manager = sensor_manager
        self.food_service = FoodService(db)
        self.points_service = PointsService(db)

        # Register intent patterns and handlers
        self.handlers: List[Dict[str, Any]] = [
            {"intent": "exit", "patterns": [r"\b(exit|quit|stop|goodbye|bye)\b"], "func": self._handle_exit},
            {"intent": "list_food", "patterns": [
                r"what(?:'s| is)? (?:do we have|in the fridge|food do i have|inside)",
                r"what do we have(?: in the fridge)?",
                r"show (?:my )?food",
                r"show fridge (?:items|food)?",
                r"how much food is left",
                r"list (?:all )?(?:items|products|food)",
                r"fridge items"
            ], "func": self._handle_list_food},
            {"intent": "expiring_today", "patterns": [
                r"what expires today",
                r"food expiring today"
            ], "func": self._handle_expiring_today},
            {"intent": "expired", "patterns": [
                r"what has expired",
                r"what is expired",
                r"expired (?:items|food)"
            ], "func": self._handle_expired},
            {"intent": "expiring_soon", "patterns": [
                r"what expires soon",
                r"what is expiring",
                r"which food expires",
                r"expiring soon",
                r"check expiry"
            ], "func": self._handle_expiring_soon},
            {"intent": "recipe_cook", "patterns": [
                r"what should i cook(?: today)?",
                r"what can i cook(?: today)?",
                r"what to cook(?: today)?",
                r"cook today",
                r"cook something(?: today)?",
                r"what recipe",
                r"suggest a recipe",
                r"recipe recommendation",
                r"recommend a recipe",
                r"^cook\b"
            ], "func": self._handle_cook_recommendation},
            {"intent": "recipe_ingredient", "patterns": [
                r"what can i cook with ([a-zA-Z]+)",
                r"recipes? for ([a-zA-Z]+)",
                r"how to cook ([a-zA-Z]+)"
            ], "func": self._handle_cook_ingredient},
            {"intent": "temperature", "patterns": [
                r"what(?:'s| is)? the temperature",
                r"fridge temperature",
                r"how cold is it"
            ], "func": self._handle_temperature},
            {"intent": "door", "patterns": [
                r"is the (?:fridge )?door open",
                r"door status",
                r"is door closed"
            ], "func": self._handle_door},
            {"intent": "points", "patterns": [
                r"how many points(?: do i have)?",
                r"my points",
                r"show points",
                r"gamification score",
                r"^points\b"
            ], "func": self._handle_points},
            {"intent": "quantity_query", "patterns": [
                r"how much ([a-zA-Z]+)(?: do i have| is left)?",
                r"how many ([a-zA-Z]+)(?: do i have| are left)?"
            ], "func": self._handle_quantity_query},
            {"intent": "consume", "patterns": [
                r"mark ([a-zA-Z]+) as consumed",
                r"i ate the ([a-zA-Z]+)",
                r"i consumed the ([a-zA-Z]+)",
                r"finished the ([a-zA-Z]+)"
            ], "func": self._handle_consume},
        ]

    def clean_query(self, query: str) -> str:
        """Strips wake word 'hey alina' and leading/trailing punctuation."""
        q = query.lower().strip()
        q = re.sub(r"^(?:hey |hi |hello )?alina[,:]?\s*", "", q)
        q = q.strip(".,?! \t\r\n")
        return q

    def process(self, query: str) -> Dict[str, Any]:
        """Dispatches query to appropriate intent handler."""
        cleaned = self.clean_query(query)
        if not cleaned:
            return {
                "intent": "empty",
                "response": "I didn't catch that. How can I assist with your fridge?",
                "data": None,
                "should_exit": False
            }

        logger.info("Processing command: '%s' (cleaned: '%s')", query, cleaned)

        for handler in self.handlers:
            for pattern in handler["patterns"]:
                match = re.search(pattern, cleaned, re.IGNORECASE)
                if match:
                    return handler["func"](cleaned, match)

        # Fallback for unrecognized intent without penalizing the user
        return {
            "intent": "unknown",
            "response": (
                "I didn't recognize that command. You can ask me what expires soon, "
                "what should I cook, how much milk is left, or check temperature and door status."
            ),
            "data": None,
            "should_exit": False
        }

    # ================= Handlers =================

    def _handle_exit(self, query: str, match: re.Match) -> Dict[str, Any]:
        return {
            "intent": "exit",
            "response": "Goodbye! Have a fresh and sustainable day.",
            "data": None,
            "should_exit": True
        }

    def _handle_list_food(self, query: str, match: re.Match) -> Dict[str, Any]:
        foods = self.food_service.list_foods(status="active")
        if not foods:
            return {
                "intent": "list_food",
                "response": "Your fridge is currently empty. You can add food items manually or scan them.",
                "data": [],
                "should_exit": False
            }

        items_summary = [f"{f['name']} ({f['quantity']} {f['unit']}, {f['days_remaining']} days left)" for f in foods[:6]]
        count = len(foods)
        resp = f"You have {count} items in your fridge: {', '.join(items_summary)}."
        return {"intent": "list_food", "response": resp, "data": foods, "should_exit": False}

    def _handle_expiring_today(self, query: str, match: re.Match) -> Dict[str, Any]:
        foods = get_expiring_today(self.db)
        if not foods:
            return {
                "intent": "expiring_today",
                "response": "Great news! No food items are expiring today.",
                "data": [],
                "should_exit": False
            }
        names = [f["name"] for f in foods]
        resp = f"Caution: {', '.join(names)} {'expires' if len(names) == 1 else 'expire'} today! Please use them today."
        return {"intent": "expiring_today", "response": resp, "data": foods, "should_exit": False}

    def _handle_expired(self, query: str, match: re.Match) -> Dict[str, Any]:
        foods = get_expired_foods(self.db)
        if not foods:
            return {
                "intent": "expired",
                "response": "You have no expired items in your fridge.",
                "data": [],
                "should_exit": False
            }
        names = [f"{f['name']} (expired {abs(f['days_remaining'])} days ago)" for f in foods]
        resp = f"Attention: {', '.join(names)}. Please check these products before use."
        return {"intent": "expired", "response": resp, "data": foods, "should_exit": False}

    def _handle_expiring_soon(self, query: str, match: re.Match) -> Dict[str, Any]:
        foods = get_expiring_soon(self.db, max_days=3)
        if not foods:
            return {
                "intent": "expiring_soon",
                "response": "None of your food items are expiring in the next 3 days. Everything is fresh!",
                "data": [],
                "should_exit": False
            }
        summaries = []
        for f in foods:
            days = f["days_remaining"]
            day_text = "today" if days == 0 else ("tomorrow" if days == 1 else f"in {days} days")
            summaries.append(f"{f['name']} expires {day_text} ({f['priority']})")

        resp = f"Items expiring soon: {', '.join(summaries)}."
        return {"intent": "expiring_soon", "response": resp, "data": foods, "should_exit": False}

    def _handle_cook_recommendation(self, query: str, match: re.Match) -> Dict[str, Any]:
        recommendation = recommend_recipe_for_fridge(self.db)
        return {
            "intent": "recipe_cook",
            "response": recommendation["message"],
            "data": recommendation,
            "should_exit": False
        }

    def _handle_cook_ingredient(self, query: str, match: re.Match) -> Dict[str, Any]:
        ingredient = match.group(1).strip().lower()
        recipes = get_recipes_for_ingredient(ingredient)
        if recipes:
            resp = f"With {ingredient}, you can make: {', '.join(recipes)}. Please check ingredient freshness before cooking."
            return {"intent": "recipe_ingredient", "response": resp, "data": recipes, "should_exit": False}
        else:
            resp = f"I do not have pre-stored recipes for {ingredient}, but you can pair it with fresh pantry staples."
            return {"intent": "recipe_ingredient", "response": resp, "data": [], "should_exit": False}

    def _handle_quantity_query(self, query: str, match: re.Match) -> Dict[str, Any]:
        ingredient = match.group(1).strip().capitalize()
        foods = self.food_service.list_foods(status="active")
        matched = [f for f in foods if ingredient.lower() in f["name"].lower()]

        if matched:
            item = matched[0]
            weight_info = f" ({item['weight_grams']} grams)" if item.get("weight_grams") else ""
            resp = f"You have {item['quantity']} {item['unit']}{weight_info} of {item['name']}. It expires in {item['days_remaining']} days."
            return {"intent": "quantity_query", "response": resp, "data": item, "should_exit": False}

        return {
            "intent": "quantity_query",
            "response": f"I couldn't find any {ingredient} currently listed in your active fridge inventory.",
            "data": None,
            "should_exit": False
        }

    def _handle_temperature(self, query: str, match: re.Match) -> Dict[str, Any]:
        if self.sensor_manager:
            status = self.sensor_manager.get_current_status()
            temp = status.get("temperature")
            if temp is not None:
                resp = f"The current fridge temperature is {temp:.1f} degrees Celsius."
            else:
                resp = "Temperature sensor is currently offline."
            return {"intent": "temperature", "response": resp, "data": status, "should_exit": False}
        return {
            "intent": "temperature",
            "response": "Sensor manager is not initialized.",
            "data": None,
            "should_exit": False
        }

    def _handle_door(self, query: str, match: re.Match) -> Dict[str, Any]:
        if self.sensor_manager:
            status = self.sensor_manager.get_current_status()
            door = status.get("door", "unknown").upper()
            resp = f"The fridge door is currently {door}."
            return {"intent": "door", "response": resp, "data": status, "should_exit": False}
        return {
            "intent": "door",
            "response": "Sensor manager is not initialized.",
            "data": None,
            "should_exit": False
        }

    def _handle_points(self, query: str, match: re.Match) -> Dict[str, Any]:
        summary = self.points_service.get_summary()
        pts = summary["current_points"]
        resp = f"You have {pts} sustainability points! Keep consuming food before expiry to earn more."
        return {"intent": "points", "response": resp, "data": summary, "should_exit": False}

    def _handle_consume(self, query: str, match: re.Match) -> Dict[str, Any]:
        ingredient = match.group(1).strip().capitalize()
        foods = self.food_service.list_foods(status="active")
        matched = [f for f in foods if ingredient.lower() in f["name"].lower()]

        if matched:
            item = matched[0]
            consumed = self.food_service.consume_food(item["id"])
            resp = f"Marked {item['name']} as consumed! You earned +10 points for preventing food waste."
            return {"intent": "consume", "response": resp, "data": consumed, "should_exit": False}

        return {
            "intent": "consume",
            "response": f"I couldn't find {ingredient} in your active inventory to mark as consumed.",
            "data": None,
            "should_exit": False
        }
