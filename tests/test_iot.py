"""
Unit tests for IoT, ESP32 Client, Temperature, and Door Sensors.
"""

from app.iot.esp32_client import ESP32Client
from app.iot.temperature import evaluate_temperature
from app.iot.door import DoorMonitor
from app.iot.weight import WeightMonitor


def test_esp32_demo_mode_and_offline():
    # In Demo Mode, client returns simulated data without crashing
    client_demo = ESP32Client(demo_mode=True)
    status_demo = client_demo.fetch_status()
    assert "temperature" in status_demo
    assert status_demo["door"] in ["closed", "open"]
    assert status_demo["demo_mode"] is True

    # In Real IoT mode with dummy unreachable IP, client fails gracefully
    client_hw = ESP32Client(ip="192.0.2.1", port=80, timeout=0.1, demo_mode=False)
    status_hw = client_hw.fetch_status()
    assert status_hw["online"] is False
    assert "offline" in status_hw["message"].lower()


def test_temperature_evaluation():
    # Optimal
    res1 = evaluate_temperature(3.5)
    assert res1["status"] == "optimal"
    assert res1["is_safe"] is True

    # High warning
    res2 = evaluate_temperature(11.0)
    assert res2["status"] == "critical_warm"
    assert res2["is_safe"] is False

    # Offline
    res3 = evaluate_temperature(None)
    assert res3["status"] == "unavailable"


def test_door_alarm_timing():
    monitor = DoorMonitor(threshold_seconds=0.1)
    # Closed
    assert monitor.update("closed")["status"] == "closed"
    assert monitor.update("closed")["should_sound_alarm"] is False

    # Open
    res_open = monitor.update("open")
    assert res_open["status"] == "open"

    # Wait a bit and update again to trigger alarm
    import time
    time.sleep(0.15)
    res_alarm = monitor.update("open")
    assert res_alarm["should_sound_alarm"] is True
    assert res_alarm["alarm_triggered"] is True

    # Close door resets alarm
    res_close = monitor.update("closed")
    assert res_close["alarm_triggered"] is False


def test_weight_monitor_jitter():
    weight_mon = WeightMonitor(jitter_threshold=10.0)
    res1 = weight_mon.process_reading(500.0)
    assert res1["weight_grams"] == 500.0

    # Small jitter < 10g should not trigger significant change
    res2 = weight_mon.process_reading(503.0)
    assert res2["is_significant_change"] is False

    # Large change > 10g triggers significant change
    res3 = weight_mon.process_reading(400.0)
    assert res3["is_significant_change"] is True
    assert res3["delta"] == 100.0
