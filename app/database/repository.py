"""
Data Access Layer (Repository Pattern) for ALINA SQLite database.
Handles CRUD for Foods, Sensor readings, Gamification points, and Events.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import Food, SensorReading, Points, Event
from app.config.settings import logger


class FoodRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        name: str,
        expiry_date: date,
        quantity: float = 1.0,
        unit: str = "pieces",
        category: str = "General",
        weight_grams: Optional[float] = None,
        added_date: Optional[date] = None,
        image_path: Optional[str] = None
    ) -> Food:
        food = Food(
            name=name.strip().capitalize(),
            category=category.strip().capitalize(),
            quantity=quantity,
            unit=unit.strip().lower(),
            weight_grams=weight_grams,
            added_date=added_date or date.today(),
            expiry_date=expiry_date,
            image_path=image_path,
            status="active"
        )
        self.db.add(food)
        self.db.commit()
        self.db.refresh(food)
        logger.info("Added food item: id=%s name='%s' expiry=%s", food.id, food.name, food.expiry_date)
        return food

    def get_by_id(self, food_id: int) -> Optional[Food]:
        return self.db.query(Food).filter(Food.id == food_id).first()

    def get_all(self, status: Optional[str] = None) -> List[Food]:
        query = self.db.query(Food)
        if status:
            query = query.filter(Food.status == status)
        return query.order_by(Food.expiry_date.asc()).all()

    def update(self, food_id: int, **kwargs) -> Optional[Food]:
        food = self.get_by_id(food_id)
        if not food:
            return None
        for key, value in kwargs.items():
            if hasattr(food, key) and value is not None:
                setattr(food, key, value)
        food.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(food)
        logger.info("Updated food item id=%s", food_id)
        return food

    def delete(self, food_id: int) -> bool:
        food = self.get_by_id(food_id)
        if not food:
            return False
        self.db.delete(food)
        self.db.commit()
        logger.info("Deleted food item id=%s", food_id)
        return True

    def mark_consumed(self, food_id: int) -> Optional[Food]:
        food = self.get_by_id(food_id)
        if not food:
            return None
        food.status = "consumed"
        food.consumed_date = date.today()
        food.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(food)
        logger.info("Marked food id=%s ('%s') as consumed", food.id, food.name)
        return food


class PointsRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, points: int, reason: str) -> Points:
        record = Points(points=points, reason=reason, timestamp=datetime.utcnow())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("Points recorded: %+d pts (reason: %s)", points, reason)
        return record

    def get_total(self) -> int:
        total = self.db.query(func.sum(Points.points)).scalar()
        return int(total) if total is not None else 100

    def get_recent(self, limit: int = 15) -> List[Points]:
        return self.db.query(Points).order_by(Points.timestamp.desc()).limit(limit).all()


class SensorRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        temperature: Optional[float],
        humidity: Optional[float],
        door_status: str,
        weight: Optional[float]
    ) -> SensorReading:
        reading = SensorReading(
            temperature=temperature,
            humidity=humidity,
            door_status=door_status,
            weight=weight,
            timestamp=datetime.utcnow()
        )
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def get_latest(self) -> Optional[SensorReading]:
        return self.db.query(SensorReading).order_by(SensorReading.timestamp.desc()).first()

    def get_recent(self, limit: int = 20) -> List[SensorReading]:
        return self.db.query(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit).all()


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, event_type: str, message: str) -> Event:
        event = Event(event_type=event_type, message=message, timestamp=datetime.utcnow())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.info("Event logged [%s]: %s", event_type, message)
        return event

    def get_recent(self, limit: int = 20) -> List[Event]:
        return self.db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()


def seed_demo_data(db: Session):
    """
    Seeds initial starting points (100) and realistic demo food items
    if the database is brand new. Expiry dates are calculated dynamically
    from today's real date, satisfying requirements.
    """
    # 1. Initialize Points if empty
    points_repo = PointsRepository(db)
    if db.query(Points).count() == 0:
        points_repo.add(100, "Initial starting points")

    # 2. Initialize Foods if empty
    food_repo = FoodRepository(db)
    if db.query(Food).count() == 0:
        today = date.today()
        demo_items = [
            {"name": "Chicken", "days": 1, "quantity": 500, "unit": "grams", "category": "Meat", "weight_grams": 500},
            {"name": "Milk", "days": 2, "quantity": 1, "unit": "litre", "category": "Dairy", "weight_grams": 1030},
            {"name": "Cheese", "days": 5, "quantity": 200, "unit": "grams", "category": "Dairy", "weight_grams": 200},
            {"name": "Apple", "days": 4, "quantity": 4, "unit": "pieces", "category": "Fruits", "weight_grams": 600},
            {"name": "Eggs", "days": 7, "quantity": 7, "unit": "pieces", "category": "Poultry", "weight_grams": 350},
        ]

        for item in demo_items:
            expiry_date = today + timedelta(days=item["days"])
            food_repo.add(
                name=item["name"],
                expiry_date=expiry_date,
                quantity=item["quantity"],
                unit=item["unit"],
                category=item["category"],
                weight_grams=item["weight_grams"]
            )

        events_repo = EventRepository(db)
        events_repo.add("SYSTEM_INIT", "Demo food items seeded with dynamic expiry dates.")
        logger.info("Demo database successfully initialized with %d food items.", len(demo_items))
