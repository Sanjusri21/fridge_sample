"""
Database Models for ALINA Smart Fridge.
Uses SQLAlchemy declarative models for Food, SensorReading, Points, and Events.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, String, Date, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Food(Base):
    __tablename__ = "food"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), default="General")
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(30), nullable=False, default="pieces")
    weight_grams = Column(Float, nullable=True)
    added_date = Column(Date, default=date.today, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    image_path = Column(String(255), nullable=True)
    status = Column(String(30), default="active", nullable=False)  # active, consumed, expired
    consumed_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "weight_grams": self.weight_grams,
            "added_date": self.added_date.isoformat() if self.added_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "image_path": self.image_path,
            "status": self.status,
            "consumed_date": self.consumed_date.isoformat() if self.consumed_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    door_status = Column(String(20), default="closed")
    weight = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "door_status": self.door_status,
            "weight": self.weight,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Points(Base):
    __tablename__ = "points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "points": self.points,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
