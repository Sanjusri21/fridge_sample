"""
Temperature Sensor Evaluator (DS18B20).
Evaluates temperature ranges and health status for domestic smart refrigerators.
"""

from typing import Dict, Any, Optional

IDEAL_TEMP_MIN = 1.0
IDEAL_TEMP_MAX = 5.0
WARNING_TEMP_HIGH = 7.0
CRITICAL_TEMP_HIGH = 10.0


def evaluate_temperature(temp_celsius: Optional[float]) -> Dict[str, Any]:
    """
    Evaluates temperature value against safe preservation thresholds.
    """
    if temp_celsius is None:
        return {
            "status": "unavailable",
            "message": "Temperature sensor is currently offline.",
            "is_safe": False,
            "value": None,
        }

    if temp_celsius < 0.0:
        return {
            "status": "freezing_warning",
            "message": f"Temperature is {temp_celsius:.1f}°C (too cold, freezing risk).",
            "is_safe": False,
            "value": temp_celsius,
        }
    elif temp_celsius <= IDEAL_TEMP_MAX:
        return {
            "status": "optimal",
            "message": f"Temperature is {temp_celsius:.1f}°C (optimal food preservation).",
            "is_safe": True,
            "value": temp_celsius,
        }
    elif temp_celsius <= WARNING_TEMP_HIGH:
        return {
            "status": "elevated",
            "message": f"Temperature is {temp_celsius:.1f}°C (slightly warm, check door seal).",
            "is_safe": True,
            "value": temp_celsius,
        }
    else:
        return {
            "status": "critical_warm",
            "message": f"Critical warning: Temperature is {temp_celsius:.1f}°C! Food spoilage risk.",
            "is_safe": False,
            "value": temp_celsius,
        }
