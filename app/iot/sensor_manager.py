"""
Sensor Manager for ALINA.
Coordinates real ESP32 polling or local realistic simulation (Demo Mode).
Evaluates door alarms, logs weight drops, and persists readings to SQLite.
"""

import time
import random
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config.settings import settings, logger
from app.iot.esp32_client import ESP32Client
from app.iot.actuators import ActuatorController
from app.iot.door import DoorMonitor
from app.iot.temperature import evaluate_temperature
from app.iot.weight import WeightMonitor
from app.database.database import SessionLocal
from app.database.repository import SensorRepository, EventRepository
from app.food.consumption import ConsumptionService


class SensorManager:
    def __init__(self, demo_mode: Optional[bool] = None):
        self.demo_mode = demo_mode if demo_mode is not None else settings.DEMO_MODE
        self.esp32 = ESP32Client(demo_mode=self.demo_mode)
        self.actuators = ActuatorController(self.esp32)
        self.door_monitor = DoorMonitor(threshold_seconds=15.0)
        self.weight_monitor = WeightMonitor(jitter_threshold=15.0)

        # Simulation state
        self.simulated_temp = 4.2
        self.simulated_humidity = 60.0
        self.simulated_door = "closed"
        self.simulated_weight = 520.0

        # Cached latest state
        self.latest_state: Dict[str, Any] = {
            "temperature": self.simulated_temp,
            "humidity": self.simulated_humidity,
            "door": self.simulated_door,
            "weight": self.simulated_weight,
            "esp32_online": False,
            "temp_eval": evaluate_temperature(self.simulated_temp),
            "door_eval": {"status": "closed", "duration_open_seconds": 0.0, "alarm_triggered": False},
            "timestamp": time.time(),
        }

    def poll_sensors(self) -> Dict[str, Any]:
        """
        Polls either real ESP32 or updates simulated environment.
        Saves reading to database and checks alarm events.
        """
        raw_temp: Optional[float] = None
        raw_humidity: Optional[float] = None
        raw_door: str = "closed"
        raw_weight: Optional[float] = None
        esp32_online = False

        if not self.demo_mode:
            hw = self.esp32.fetch_status()
            esp32_online = hw.get("online", False)
            if esp32_online:
                raw_temp = hw.get("temperature")
                raw_humidity = hw.get("humidity")
                raw_door = hw.get("door", "closed")
                raw_weight = hw.get("weight")
            else:
                # ESP32 offline fallback
                raw_temp = self.latest_state.get("temperature", 4.0)
                raw_humidity = self.latest_state.get("humidity", 55.0)
                raw_door = self.latest_state.get("door", "closed")
                raw_weight = self.latest_state.get("weight", 500.0)
        else:
            # Realistic slight variations in demo mode
            self.simulated_temp = round(4.0 + random.uniform(-0.3, 0.3), 1)
            self.simulated_humidity = round(60.0 + random.uniform(-1.5, 1.5), 1)
            raw_temp = self.simulated_temp
            raw_humidity = self.simulated_humidity
            raw_door = self.simulated_door
            raw_weight = self.simulated_weight
            esp32_online = False

        # Evaluate door status and alarm
        door_result = self.door_monitor.update(raw_door)
        if door_result["should_sound_alarm"]:
            logger.warning("Door alarm triggered! Activating buzzer and warning LED.")
            self.actuators.set_buzzer(True)
            self.actuators.set_led_status("CRITICAL")

        # Evaluate temperature
        temp_eval = evaluate_temperature(raw_temp)

        # Check weight changes for food consumption
        weight_result = self.weight_monitor.process_reading(raw_weight)
        if weight_result["is_significant_change"] and weight_result.get("previous_weight"):
            prev_w = weight_result["previous_weight"]
            curr_w = weight_result["weight_grams"]
            if prev_w > curr_w:
                db = SessionLocal()
                try:
                    consumption_svc = ConsumptionService(db)
                    consumption_svc.detect_weight_change(prev_w, curr_w)
                finally:
                    db.close()

        # Update cached state
        self.latest_state = {
            "temperature": raw_temp,
            "humidity": raw_humidity,
            "door": raw_door,
            "weight": raw_weight,
            "esp32_online": esp32_online,
            "temp_eval": temp_eval,
            "door_eval": door_result,
            "actuators": self.actuators.get_state(),
            "timestamp": time.time(),
        }

        # Persist reading to database
        db = SessionLocal()
        try:
            repo = SensorRepository(db)
            repo.add(
                temperature=raw_temp,
                humidity=raw_humidity,
                door_status=raw_door,
                weight=raw_weight
            )
        except Exception as e:
            logger.error("Failed to persist sensor reading: %s", e)
        finally:
            db.close()

        return self.latest_state

    def get_current_status(self) -> Dict[str, Any]:
        """Returns the latest sensor state."""
        return self.latest_state

    def simulate_set_door(self, status: str) -> Dict[str, Any]:
        """Manually toggle simulated door for testing."""
        self.simulated_door = status.lower()
        if self.simulated_door == "closed":
            self.actuators.set_buzzer(False)
            self.actuators.set_led_status("NORMAL")
        return self.poll_sensors()

    def simulate_set_weight(self, weight_grams: float) -> Dict[str, Any]:
        """Manually set simulated weight to test consumption detection."""
        self.simulated_weight = float(weight_grams)
        return self.poll_sensors()

    def simulate_set_temperature(self, temp_c: float) -> Dict[str, Any]:
        """Manually set simulated temperature."""
        self.simulated_temp = float(temp_c)
        return self.poll_sensors()
