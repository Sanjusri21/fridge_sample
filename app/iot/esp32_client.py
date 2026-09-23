"""
ESP32 Wi-Fi HTTP Client for ALINA.
Communicates with ESP32 microcontroller over local network.
Fails gracefully with timeout without hanging or crashing.
"""

from typing import Dict, Any, Optional
import requests
from app.config.settings import settings, logger


class ESP32Client:
    def __init__(
        self,
        ip: Optional[str] = None,
        port: Optional[int] = None,
        timeout: Optional[float] = None,
        demo_mode: Optional[bool] = None,
    ):
        self.ip = ip or settings.ESP32_IP
        self.port = port or settings.ESP32_PORT
        self.timeout = timeout or settings.ESP32_TIMEOUT
        self.demo_mode = demo_mode if demo_mode is not None else settings.DEMO_MODE
        self.base_url = f"http://{self.ip}:{self.port}"
        self.is_online = False
        self.last_known_data: Dict[str, Any] = {
            "temperature": 4.2,
            "humidity": 60.0,
            "door": "closed",
            "weight": 520.0,
            "online": False,
        }

    def fetch_status(self) -> Dict[str, Any]:
        """
        Polls ESP32 /status endpoint.
        Returns sensor readings dictionary and online status.
        """
        if self.demo_mode:
            return {
                **self.last_known_data,
                "online": False,
                "demo_mode": True,
                "message": "Demo Mode active: Hardware ESP32 simulated.",
            }

        try:
            url = f"{self.base_url}/status"
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                self.is_online = True
                self.last_known_data = {
                    "temperature": float(data.get("temperature", 4.0)),
                    "humidity": float(data.get("humidity", 50.0)),
                    "door": str(data.get("door", "closed")).lower(),
                    "weight": float(data.get("weight", 0.0)),
                    "online": True,
                    "demo_mode": False,
                    "message": "ESP32 online.",
                }
                return self.last_known_data
            else:
                self.is_online = False
                logger.warning("ESP32 responded with status %s", resp.status_code)
        except Exception as e:
            self.is_online = False
            logger.info("ESP32 offline or unreachable (%s): %s", self.base_url, e)

        return {
            **self.last_known_data,
            "online": False,
            "demo_mode": False,
            "message": "ESP32 offline – using last known data",
        }

    def send_command(self, command: str) -> Dict[str, Any]:
        """
        Sends an actuator command to the ESP32 /command endpoint.
        """
        if self.demo_mode:
            return {"success": True, "command": command, "note": "Simulated in Demo Mode"}

        try:
            url = f"{self.base_url}/command"
            resp = requests.post(url, json={"action": command}, timeout=self.timeout)
            if resp.status_code == 200:
                return {"success": True, "command": command, "response": resp.json()}
        except Exception as e:
            logger.warning("Failed to send command '%s' to ESP32: %s", command, e)

        return {"success": False, "command": command, "error": "ESP32 offline"}
