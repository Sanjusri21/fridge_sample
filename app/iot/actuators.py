"""
Actuator Controller for ALINA.
Controls Buzzer, Status LEDs (Normal, Warning, Critical), Servo, and simulated relay.
Dispatches commands to ESP32 or simulates actions in Demo Mode.
"""

from typing import Dict, Any, Optional
from app.config.settings import logger


class ActuatorController:
    def __init__(self, esp32_client=None):
        self.esp32_client = esp32_client
        self.state = {
            "buzzer": False,
            "led_state": "NORMAL",  # NORMAL (Green), WARNING (Yellow), CRITICAL (Red)
            "servo_position": "CLOSED",  # OPEN or CLOSED
            "relay_demo_load": False,  # STRICTLY low-voltage demonstration load only
        }

    def set_buzzer(self, on: bool) -> Dict[str, Any]:
        """Toggles the alert buzzer."""
        self.state["buzzer"] = on
        cmd = "BUZZER_ON" if on else "BUZZER_OFF"
        logger.info("Actuator command: %s", cmd)

        if self.esp32_client and not self.esp32_client.demo_mode:
            self.esp32_client.send_command(cmd)

        return {"buzzer": on, "command": cmd}

    def set_led_status(self, level: str) -> Dict[str, Any]:
        """
        Sets status LED level: 'NORMAL', 'WARNING', 'CRITICAL'.
        """
        level_upper = level.upper()
        if level_upper not in ["NORMAL", "WARNING", "CRITICAL"]:
            level_upper = "NORMAL"

        self.state["led_state"] = level_upper
        cmd = f"LED_{level_upper}"
        logger.info("Actuator command: %s", cmd)

        if self.esp32_client and not self.esp32_client.demo_mode:
            self.esp32_client.send_command(cmd)

        return {"led_state": level_upper, "command": cmd}

    def set_servo(self, open_door: bool) -> Dict[str, Any]:
        """Controls mechanical demo servo latch."""
        pos = "OPEN" if open_door else "CLOSED"
        self.state["servo_position"] = pos
        cmd = f"SERVO_{pos}"
        logger.info("Actuator command: %s", cmd)

        if self.esp32_client and not self.esp32_client.demo_mode:
            self.esp32_client.send_command(cmd)

        return {"servo_position": pos, "command": cmd}

    def set_relay_demo(self, on: bool) -> Dict[str, Any]:
        """
        Controls demonstration-only low voltage DC load.
        NOTE: Never control mains 230V power.
        """
        self.state["relay_demo_load"] = on
        cmd = "RELAY_ON" if on else "RELAY_OFF"
        logger.info("Demo relay command (low-voltage only): %s", cmd)

        if self.esp32_client and not self.esp32_client.demo_mode:
            self.esp32_client.send_command(cmd)

        return {"relay_demo_load": on, "command": cmd}

    def get_state(self) -> Dict[str, Any]:
        return dict(self.state)
