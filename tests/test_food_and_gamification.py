"""
Unit tests for Food Inventory, Gamification Points, and Recipes.
"""

from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.food.inventory import FoodService
from app.gamification.points import PointsService
from app.ai.recipes import get_recipes_for_ingredient
from app.ai.recommendations import recommend_recipe_for_fridge


def get_test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


def test_food_crud_and_points_reward():
    db = get_test_db()
    points_svc = PointsService(db)
    points_svc.record_custom(100, "Initial starting points")
    assert points_svc.get_summary()["current_points"] == 100

    food_svc = FoodService(db)

    # Add Food
    tomorrow = date.today() + timedelta(days=1)
    item = food_svc.add_food(
        name="Chicken",
        expiry_date=tomorrow,
        quantity=500,
        unit="grams",
        category="Meat"
    )
    assert item["name"] == "Chicken"
    assert item["days_remaining"] == 1
    assert item["priority"] == "CRITICAL"

    # Consume Food before expiry -> should reward +10 points
    consumed = food_svc.consume_food(item["id"])
    assert consumed["status"] == "consumed"

    # Verify points updated to 110
    assert points_svc.get_summary()["current_points"] == 110


def test_recipe_recommendation_prioritizes_soonest_expiry():
    db = get_test_db()
    food_svc = FoodService(db)

    today = date.today()
    # Add milk expiring in 5 days
    food_svc.add_food(name="Milk", expiry_date=today + timedelta(days=5))
    # Add chicken expiring tomorrow (1 day)
    food_svc.add_food(name="Chicken", expiry_date=today + timedelta(days=1))

    recommendation = recommend_recipe_for_fridge(db)
    assert recommendation["food_item"]["name"] == "Chicken"
    assert "Chicken" in recommendation["message"]
    assert len(recommendation["all_recipes"]) > 0
