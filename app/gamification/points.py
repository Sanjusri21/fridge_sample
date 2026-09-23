"""
ALINA Gamification & Food Waste Reduction Points Service.
Tracks points, rewards mindful consumption, and prevents food waste penalties.
Rules:
- Initial points: 100
- Food consumed before expiry: +10
- User responds to reminder: +5
- Food expires unused: -10
- Unknown/unrecognized request: No penalty (0 pts)
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.repository import PointsRepository, EventRepository
from app.config.settings import logger


class PointsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PointsRepository(db)
        self.event_repo = EventRepository(db)

    def get_summary(self) -> Dict[str, Any]:
        """Returns current total points and recent transactions."""
        total = self.repo.get_total()
        recent = self.repo.get_recent(limit=10)
        return {
            "current_points": total,
            "recent_changes": [r.to_dict() for r in recent],
        }

    def reward_consumed_before_expiry(self, food_name: str) -> int:
        """Reward +10 when food is used before it goes to waste."""
        self.repo.add(10, f"Food consumed before expiry: {food_name}")
        self.event_repo.add("POINTS_AWARDED", f"+10 points: consumed '{food_name}' before expiry")
        return self.repo.get_total()

    def reward_reminder_response(self, reminder_topic: str) -> int:
        """Reward +5 when user acts on an expiry reminder."""
        self.repo.add(5, f"Responded to expiry reminder: {reminder_topic}")
        self.event_repo.add("POINTS_AWARDED", f"+5 points: acted on reminder for '{reminder_topic}'")
        return self.repo.get_total()

    def penalize_expired_unused(self, food_name: str) -> int:
        """Deduct 10 points when food expires without being consumed."""
        self.repo.add(-10, f"Food expired unused: {food_name}")
        self.event_repo.add("POINTS_PENALTY", f"-10 points: '{food_name}' expired unused")
        return self.repo.get_total()

    def record_custom(self, points: int, reason: str) -> int:
        """Records an explicit points adjustment."""
        self.repo.add(points, reason)
        self.event_repo.add("POINTS_CHANGE", f"{points:+d} points: {reason}")
        return self.repo.get_total()
