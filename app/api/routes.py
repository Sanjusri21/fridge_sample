"""
FastAPI REST API Routes for ALINA Smart Fridge.
Implements complete CRUD, AI assistant queries, sensor status, OCR scanning, and gamification.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.database.repository import EventRepository
from app.food.inventory import FoodService
from app.food.expiry import get_expiring_soon, get_expired_foods
from app.food.consumption import ConsumptionService
from app.gamification.points import PointsService
from app.vision.camera import CameraManager
from app.vision.ocr import run_ocr, check_tesseract_installed
from app.voice.listener import check_microphone_available
from app.voice.speaker import check_speaker_available
from app.ai.assistant import AlinaAssistant
from app.config.settings import settings, logger
from app.api.schemas import (
    FoodCreate, FoodUpdate, AskRequest, AskResponse,
    ScanResponse, SimulateSensorsRequest, ActuatorControlRequest,
    ConsumptionConfirmRequest
)

router = APIRouter(prefix="/api", tags=["ALINA API"])

# Global singletons managed by app.main
_sensor_manager = None
_camera_manager = CameraManager()


def set_sensor_manager(sm):
    global _sensor_manager
    _sensor_manager = sm


# ================= Health & System Status =================

@router.get("/health")
def get_health():
    return {"status": "ok", "service": "ALINA Smart Fridge Voice Assistant"}


@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    """
    Returns system diagnostic status for all hardware and software components.
    """
    # 1. Database status
    db_status = "ONLINE"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning("Database check failed: %s", e)
        db_status = "OFFLINE"

    # 2. Camera status
    cam_info = _camera_manager.check_availability()
    cam_status = "AVAILABLE" if cam_info["available"] else "UNAVAILABLE"

    # 3. Microphone status
    mic_info = check_microphone_available()
    mic_status = "AVAILABLE" if mic_info["available"] else "UNAVAILABLE"

    # 4. Speaker status
    spk_info = check_speaker_available()
    spk_status = "AVAILABLE" if spk_info["available"] else "UNAVAILABLE"

    # 5. OCR status
    tess_info = check_tesseract_installed()
    ocr_status = "AVAILABLE" if tess_info["available"] else "UNAVAILABLE (Manual Entry Active)"

    # 6. ESP32 & Sensors
    esp32_status = "OFFLINE (Demo Mode)" if settings.DEMO_MODE else "OFFLINE"
    temp_status = "ONLINE (Simulated)" if settings.DEMO_MODE else "OFFLINE"
    door_status = "ONLINE (Simulated)" if settings.DEMO_MODE else "OFFLINE"
    weight_status = "ONLINE (Simulated)" if settings.DEMO_MODE else "OFFLINE"

    if _sensor_manager:
        s = _sensor_manager.get_current_status()
        if s.get("esp32_online"):
            esp32_status = "ONLINE"
            temp_status = "ONLINE"
            door_status = "ONLINE"
            weight_status = "ONLINE"

    # 7. AI
    ai_status = "LOCAL DETERMINISTIC"
    if settings.AI_PROVIDER != "none" and settings.AI_API_KEY:
        ai_status = f"API ({settings.AI_PROVIDER.upper()})"

    return {
        "database": db_status,
        "camera": cam_status,
        "camera_details": cam_info["message"],
        "microphone": mic_status,
        "microphone_details": mic_info["message"],
        "speaker": spk_status,
        "speaker_details": spk_info["engine"],
        "esp32": esp32_status,
        "temperature_sensor": temp_status,
        "door_sensor": door_status,
        "weight_sensor": weight_status,
        "ocr": ocr_status,
        "ocr_details": tess_info.get("reason", ""),
        "ai": ai_status,
        "demo_mode": settings.DEMO_MODE,
    }


# ================= Food Inventory CRUD =================

@router.get("/foods")
def list_foods(status: Optional[str] = "active", db: Session = Depends(get_db)):
    """Retrieves all food items with dynamic days remaining and priority."""
    svc = FoodService(db)
    return svc.list_foods(status=status)


@router.post("/foods", status_code=status.HTTP_201_CREATED)
def add_food(food: FoodCreate, db: Session = Depends(get_db)):
    """Adds a new food item to inventory."""
    svc = FoodService(db)
    result = svc.add_food(
        name=food.name,
        expiry_date=food.expiry_date,
        quantity=food.quantity,
        unit=food.unit,
        category=food.category,
        weight_grams=food.weight_grams,
        image_path=food.image_path
    )
    return result


@router.get("/foods/{food_id}")
def get_food(food_id: int, db: Session = Depends(get_db)):
    """Retrieves a single food item by ID."""
    svc = FoodService(db)
    food = svc.get_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    return food


@router.put("/foods/{food_id}")
def update_food(food_id: int, payload: FoodUpdate, db: Session = Depends(get_db)):
    """Updates food item details."""
    svc = FoodService(db)
    updated = svc.update_food(food_id, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Food item not found")
    return updated


@router.delete("/foods/{food_id}")
def delete_food(food_id: int, db: Session = Depends(get_db)):
    """Deletes a food item from inventory."""
    svc = FoodService(db)
    success = svc.delete_food(food_id)
    if not success:
        raise HTTPException(status_code=404, detail="Food item not found")
    return {"message": "Food item successfully deleted."}


@router.post("/foods/{food_id}/consume")
def consume_food(food_id: int, db: Session = Depends(get_db)):
    """Marks food as consumed and awards gamification points."""
    svc = FoodService(db)
    result = svc.consume_food(food_id)
    if not result:
        raise HTTPException(status_code=404, detail="Food item not found or already consumed.")
    return result


@router.get("/foods/expiring")
def get_expiring_foods(days: int = 3, db: Session = Depends(get_db)):
    """Lists items expiring within the specified days."""
    return get_expiring_soon(db, max_days=days)


@router.get("/foods/expired")
def get_expired_foods_list(db: Session = Depends(get_db)):
    """Lists items that have passed their expiry date."""
    return get_expired_foods(db)


# ================= Sensors & Actuators =================

@router.get("/sensors")
def get_sensor_readings():
    """Returns current live or simulated sensor readings."""
    if _sensor_manager:
        state = _sensor_manager.get_current_status()
        return {
            **state,
            "demo_mode": settings.DEMO_MODE,
        }
    return {
        "temperature": 4.2,
        "humidity": 60.0,
        "door": "closed",
        "weight": 520.0,
        "esp32_online": False,
        "demo_mode": settings.DEMO_MODE,
    }


@router.post("/sensors/simulate")
def simulate_sensor_state(req: SimulateSensorsRequest):
    """Allows web dashboard in Demo Mode to simulate door opening or weight change."""
    if not _sensor_manager:
        raise HTTPException(status_code=500, detail="Sensor manager not initialized.")

    if req.door is not None:
        _sensor_manager.simulate_set_door(req.door)
    if req.weight is not None:
        _sensor_manager.simulate_set_weight(req.weight)
    if req.temperature is not None:
        _sensor_manager.simulate_set_temperature(req.temperature)

    return _sensor_manager.get_current_status()


@router.post("/actuators/control")
def control_actuators(req: ActuatorControlRequest):
    """Triggers actuator commands (Buzzer, LEDs, Servo)."""
    if not _sensor_manager:
        raise HTTPException(status_code=500, detail="Sensor manager not initialized.")

    actuators = _sensor_manager.actuators
    action = req.action.upper()

    if action == "BUZZER_ON":
        return actuators.set_buzzer(True)
    elif action == "BUZZER_OFF":
        return actuators.set_buzzer(False)
    elif action.startswith("LED_"):
        level = action.replace("LED_", "")
        return actuators.set_led_status(level)
    elif action == "SERVO_OPEN":
        return actuators.set_servo(True)
    elif action == "SERVO_CLOSE":
        return actuators.set_servo(False)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported actuator action: {action}")


# ================= Points & Gamification =================

@router.get("/points")
def get_points(db: Session = Depends(get_db)):
    """Returns current points total and recent point changes with reasons."""
    svc = PointsService(db)
    return svc.get_summary()


# ================= Voice & Assistant =================

@router.post("/ask", response_model=AskResponse)
def ask_alina(req: AskRequest, db: Session = Depends(get_db)):
    """
    Submits a natural language query to ALINA via text or transcribed speech.
    Returns the answer and optionally speaks via TTS.
    Guarantees valid JSON response and alina_state.
    """
    try:
        assistant = AlinaAssistant(db, sensor_manager=_sensor_manager)
        result = assistant.ask(req.query, speak_output=req.speak_output)

        intent = result.get("intent", "unknown")
        if intent in ("recipe_cook", "recipe_ingredient", "list_food"):
            alina_state = "happy"
        elif intent in ("expiring_soon", "expiring_today"):
            alina_state = "concerned"
        elif intent in ("expired", "door"):
            alina_state = "warning"
        elif intent in ("points", "consume"):
            alina_state = "celebration"
        elif intent == "unknown":
            alina_state = "concerned"
        else:
            alina_state = "happy"

        resp_text = result.get("response", "")

        return AskResponse(
            success=True,
            query=req.query,
            response=resp_text,
            message=resp_text,
            intent=intent,
            alina_state=alina_state,
            data=result.get("data"),
            should_exit=result.get("should_exit", False)
        )
    except Exception as e:
        logger.exception("Error in /api/ask endpoint: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "query": req.query,
                "response": "I couldn't process that request right now.",
                "message": "I couldn't process that request right now.",
                "intent": "error",
                "alina_state": "error",
                "error": str(e),
                "data": None,
                "should_exit": False
            }
        )


# ================= Camera & Vision OCR =================

@router.post("/scan")
def scan_food(db: Session = Depends(get_db)):
    """
    Captures frame from laptop webcam and runs OCR text + expiry extraction.
    Allows user to review and correct results before saving.
    """
    cam_info = _camera_manager.check_availability()
    if not cam_info["available"]:
        return {
            "success": False,
            "ocr_available": False,
            "raw_text": "",
            "detected_food": None,
            "detected_category": "General",
            "default_unit": "pieces",
            "default_qty": 1.0,
            "detected_expiry": None,
            "image_path": None,
            "status_message": "Camera is unavailable. You can enter food details manually.",
            "installation_guide": None
        }

    success, filepath, frame = _camera_manager.capture_frame(save=True)
    if not success or frame is None:
        return {
            "success": False,
            "ocr_available": False,
            "raw_text": "",
            "detected_food": None,
            "detected_category": "General",
            "default_unit": "pieces",
            "default_qty": 1.0,
            "detected_expiry": None,
            "image_path": None,
            "status_message": "Failed to capture image frame from camera. Enter details manually.",
            "installation_guide": None
        }

    ocr_result = run_ocr(frame)
    return {
        "success": True,
        "image_path": filepath,
        **ocr_result
    }


# ================= Weight Consumption Confirmation =================

@router.post("/consumption/confirm")
def confirm_consumption(req: ConsumptionConfirmRequest, db: Session = Depends(get_db)):
    """Confirms or cancels consumption associated with detected scale weight reduction."""
    svc = ConsumptionService(db)
    return svc.confirm_consumption(
        food_id=req.food_id,
        confirmed=req.confirmed,
        consumed_weight_grams=req.consumed_weight_grams
    )


# ================= Event Log =================

@router.get("/events")
def get_events(limit: int = 15, db: Session = Depends(get_db)):
    """Lists recent system audit events."""
    repo = EventRepository(db)
    events = repo.get_recent(limit=limit)
    return [e.to_dict() for e in events]
