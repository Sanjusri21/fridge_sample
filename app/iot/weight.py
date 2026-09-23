"""
Weight Sensor Processing (HX711 Load Cell).
Smooths readings and handles load cell calibration/tare offsets.
"""

from typing import Optional, Dict, Any


class WeightMonitor:
    def __init__(self, jitter_threshold: float = 8.0):
        self.jitter_threshold = jitter_threshold
        self.last_stable_weight: Optional[float] = None

    def process_reading(self, raw_weight: Optional[float]) -> Dict[str, Any]:
        """
        Filters noise and reports significant weight updates.
        """
        if raw_weight is None:
            return {
                "weight_grams": None,
                "status": "offline",
                "delta": 0.0,
                "is_significant_change": False,
            }

        clamped_weight = max(0.0, round(raw_weight, 1))

        if self.last_stable_weight is None:
            self.last_stable_weight = clamped_weight
            return {
                "weight_grams": clamped_weight,
                "status": "initialized",
                "delta": 0.0,
                "is_significant_change": False,
            }

        delta = self.last_stable_weight - clamped_weight
        significant = abs(delta) >= self.jitter_threshold

        if significant:
            prev = self.last_stable_weight
            self.last_stable_weight = clamped_weight
            return {
                "weight_grams": clamped_weight,
                "status": "updated",
                "delta": round(delta, 1),
                "previous_weight": prev,
                "is_significant_change": True,
            }

        return {
            "weight_grams": self.last_stable_weight,
            "status": "stable",
            "delta": 0.0,
            "is_significant_change": False,
        }
