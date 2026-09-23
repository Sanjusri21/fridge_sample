"""
Pydantic Data Schemas for ALINA FastAPI API.
Provides type validation, clear documentation, and standard responses.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ================= Food Schemas =================

class FoodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Chicken")
    expiry_date: date = Field(..., example="2026-09-20")
    quantity: float = Field(default=1.0, ge=0.01, example=500.0)
    unit: str = Field(default="pieces", example="grams")
    category: str = Field(default="General", example="Meat")
    weight_grams: Optional[float] = Field(default=None, example=500.0)
    image_path: Optional[str] = Field(default=None)


class FoodUpdate(BaseModel):
    name: Optional[str] = None
    expiry_date: Optional[date] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    weight_grams: Optional[float] = None
    status: Optional[str] = None


class FoodResponse(BaseModel):
    id: int
    name: str
    category: str
    quantity: float
    unit: str
    weight_grams: Optional[float]
    added_date: Optional[str]
    expiry_date: str
    image_path: Optional[str]
    status: str
    consumed_date: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    days_remaining: int
    priority: str


# ================= Query / Assistant Schemas =================

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, example="What expires soon?")
    speak_output: bool = Field(default=True)


class AskResponse(BaseModel):
    success: bool = True
    query: str
    response: str
    message: Optional[str] = None
    intent: str
    alina_state: str = "happy"
    data: Optional[Any] = None
    should_exit: bool = False


# ================= OCR / Scan Schemas =================

class ScanResponse(BaseModel):
    ocr_available: bool
    raw_text: str
    detected_food: Optional[str] = None
    detected_category: str = "General"
    default_unit: str = "pieces"
    default_qty: float = 1.0
    detected_expiry: Optional[str] = None
    image_path: Optional[str] = None
    status_message: str
    installation_guide: Optional[str] = None


# ================= Sensor & Actuator Schemas =================

class SensorStatusResponse(BaseModel):
    temperature: Optional[float]
    humidity: Optional[float]
    door: str
    weight: Optional[float]
    esp32_online: bool
    demo_mode: bool
    temp_eval: Dict[str, Any]
    door_eval: Dict[str, Any]
    actuators: Dict[str, Any]
    timestamp: float


class SimulateSensorsRequest(BaseModel):
    door: Optional[str] = None  # "open" or "closed"
    weight: Optional[float] = None
    temperature: Optional[float] = None


class ActuatorControlRequest(BaseModel):
    action: str = Field(..., example="BUZZER_ON")  # BUZZER_ON/OFF, LED_NORMAL/WARNING/CRITICAL, SERVO_OPEN/CLOSE


class ConsumptionConfirmRequest(BaseModel):
    food_id: int
    confirmed: bool
    consumed_weight_grams: Optional[float] = None


# ================= System Status Schemas =================

class SystemStatusResponse(BaseModel):
    database: str
    camera: str
    microphone: str
    speaker: str
    esp32: str
    temperature_sensor: str
    door_sensor: str
    weight_sensor: str
    ocr: str
    ai_provider: str
    demo_mode: bool
