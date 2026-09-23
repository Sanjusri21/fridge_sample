"""
Door Sensor (Magnetic Reed Switch) Monitor.
Tracks door status and durations. Triggers alarm warning if door left open too long.
"""

import time
from typing import Dict, Any, Optional
from app.config.settings import logger

DOOR_ALARM_THRESHOLD_SECONDS = 15.0  # Alert if open > 15s in demo


class DoorMonitor:
    def __init__(self, threshold_seconds: float = DOOR_ALARM_THRESHOLD_SECONDS):
        self.threshold_seconds = threshold_seconds
        self.door_status: str = "closed"
        self.opened_timestamp: Optional[float] = None
        self.alarm_triggered: bool = False

    def update(self, new_status: str) -> Dict[str, Any]:
        """
        Updates door status ('open' or 'closed') and calculates alarm state.
        """
        status = new_status.lower()
        now = time.time()
        should_alarm = False
        duration_open = 0.0

        if status == "open":
            if self.door_status != "open":
                # Door just opened
                self.opened_timestamp = now
                self.alarm_triggered = False
                logger.info("Fridge door opened.")

            duration_open = now - (self.opened_timestamp or now)
            if duration_open >= self.threshold_seconds and not self.alarm_triggered:
                should_alarm = True
                self.alarm_triggered = True
                logger.warning("Fridge door open for %.1f seconds! Alarm triggered.", duration_open)
        else:
            if self.door_status == "open":
                logger.info("Fridge door closed.")
            self.opened_timestamp = None
            self.alarm_triggered = False

        self.door_status = status

        return {
            "status": self.door_status,
            "duration_open_seconds": round(duration_open, 1),
            "alarm_triggered": self.alarm_triggered,
            "should_sound_alarm": should_alarm,
        }
