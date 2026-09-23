"""
Comprehensive verification script for ALINA Smart Fridge.
Tests live application endpoints at http://127.0.0.1:8000.
"""

import sys
import time
import requests
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000"

def run_verifications():
    print("--- Starting ALINA Verification Suite ---")
    results = {}

    # 1. Dashboard loads at http://127.0.0.1:8000
    try:
        r = requests.get(BASE_URL, timeout=5)
        results["1. Dashboard loads"] = (r.status_code == 200 and "ALINA" in r.text, f"HTTP {r.status_code}")
    except Exception as e:
        results["1. Dashboard loads"] = (False, str(e))

    # 2. SQLite database initializes
    try:
        r = requests.get(f"{BASE_URL}/api/status", timeout=5)
        data = r.json()
        db_ok = r.status_code == 200 and data.get("database") == "ONLINE"
        results["2. SQLite database initializes"] = (db_ok, f"Status: {data.get('database')}")
    except Exception as e:
        results["2. SQLite database initializes"] = (False, str(e))

    # 3. Demo data loads
    # 5. GET /api/foods works
    try:
        r = requests.get(f"{BASE_URL}/api/foods", timeout=5)
        foods = r.json()
        has_demo = len(foods) > 0 and any("Chicken" in f["name"] for f in foods)
        results["3. Demo data loads"] = (has_demo, f"{len(foods)} items loaded")
        results["5. GET /api/foods works"] = (r.status_code == 200, f"HTTP {r.status_code}, {len(foods)} items")
    except Exception as e:
        results["3. Demo data loads"] = (False, str(e))
        results["5. GET /api/foods works"] = (False, str(e))

    # 4. GET /api/health works
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        results["4. GET /api/health works"] = (r.status_code == 200 and r.json().get("status") == "ok", f"HTTP {r.status_code}, {r.json()}")
    except Exception as e:
        results["4. GET /api/health works"] = (False, str(e))

    # 6. GET /api/sensors works in DEMO_MODE
    try:
        r = requests.get(f"{BASE_URL}/api/sensors", timeout=5)
        s = r.json()
        sensors_ok = r.status_code == 200 and s.get("demo_mode") is True and "temperature" in s
        results["6. GET /api/sensors works in DEMO_MODE"] = (sensors_ok, f"Temp: {s.get('temperature')}°C, Door: {s.get('door')}, Demo: {s.get('demo_mode')}")
    except Exception as e:
        results["6. GET /api/sensors works in DEMO_MODE"] = (False, str(e))

    # 7. Add food works
    added_id = None
    try:
        target_expiry = (date.today() + timedelta(days=3)).isoformat()
        payload = {
            "name": "Verification Yogurt",
            "quantity": 2.0,
            "unit": "cups",
            "expiry_date": target_expiry,
            "category": "Dairy"
        }
        r = requests.post(f"{BASE_URL}/api/foods", json=payload, timeout=5)
        added_data = r.json()
        added_id = added_data.get("id")
        results["7. Add food works"] = (r.status_code == 201 and added_id is not None, f"Added ID {added_id}: {added_data.get('name')}")
    except Exception as e:
        results["7. Add food works"] = (False, str(e))

    # 10. Expiry calculation uses actual dates
    try:
        # Check added food has days_remaining == 3
        r = requests.get(f"{BASE_URL}/api/foods/{added_id}", timeout=5)
        f_data = r.json()
        expiry_ok = f_data.get("days_remaining") == 3 and f_data.get("priority") == "HIGH"
        results["10. Expiry calculation uses actual dates"] = (expiry_ok, f"Days remaining: {f_data.get('days_remaining')}, Priority: {f_data.get('priority')}")
    except Exception as e:
        results["10. Expiry calculation uses actual dates"] = (False, str(e))

    # 9. Consume food works
    try:
        r = requests.post(f"{BASE_URL}/api/foods/{added_id}/consume", timeout=5)
        c_data = r.json()
        consume_ok = r.status_code == 200 and c_data.get("status") == "consumed"
        results["9. Consume food works"] = (consume_ok, f"Status: {c_data.get('status')}, Consumed date: {c_data.get('consumed_date')}")
    except Exception as e:
        results["9. Consume food works"] = (False, str(e))

    # 8. Delete food works
    try:
        r = requests.delete(f"{BASE_URL}/api/foods/{added_id}", timeout=5)
        del_ok = r.status_code == 200
        # Verify 404
        r_chk = requests.get(f"{BASE_URL}/api/foods/{added_id}", timeout=5)
        results["8. Delete food works"] = (del_ok and r_chk.status_code == 404, "Deleted and verified 404")
    except Exception as e:
        results["8. Delete food works"] = (False, str(e))

    # 11. Recipe recommendation works
    try:
        r = requests.post(f"{BASE_URL}/api/ask", json={"query": "What should I cook today?", "speak_output": False}, timeout=5)
        ask_data = r.json()
        rec_ok = r.status_code == 200 and ask_data.get("intent") == "recipe_cook" and len(ask_data.get("response")) > 0
        results["11. Recipe recommendation works"] = (rec_ok, f"Response: {ask_data.get('response')[:60]}...")
    except Exception as e:
        results["11. Recipe recommendation works"] = (False, str(e))

    # 12. Voice command parsing works
    try:
        r = requests.post(f"{BASE_URL}/api/ask", json={"query": "Hey Alina, what expires soon?", "speak_output": False}, timeout=5)
        v_data = r.json()
        voice_ok = r.status_code == 200 and v_data.get("intent") == "expiring_soon"
        results["12. Voice command parsing works"] = (voice_ok, f"Intent: {v_data.get('intent')}, Response: {v_data.get('response')[:60]}...")
    except Exception as e:
        results["12. Voice command parsing works"] = (False, str(e))

    # 13. Camera endpoint does not crash when camera is unavailable
    try:
        r = requests.post(f"{BASE_URL}/api/scan", timeout=8)
        scan_data = r.json()
        # Should return 200 without crashing
        results["13. Camera endpoint does not crash"] = (r.status_code == 200, f"HTTP {r.status_code}, Status: {scan_data.get('status_message')}")
    except Exception as e:
        results["13. Camera endpoint does not crash"] = (False, str(e))

    # 14. OCR gracefully handles missing Tesseract
    try:
        from app.vision.ocr import run_ocr, check_tesseract_installed
        tess_info = check_tesseract_installed()
        ocr_res = run_ocr(None)
        results["14. OCR gracefully handles missing Tesseract"] = (isinstance(ocr_res, dict) and "status_message" in ocr_res, f"Handled gracefully: {ocr_res.get('status_message')[:60]}")
    except Exception as e:
        results["14. OCR gracefully handles missing Tesseract"] = (False, str(e))

    # 15. ESP32 offline mode does not crash the application
    try:
        from app.iot.esp32_client import ESP32Client
        hw_client = ESP32Client(ip="192.0.2.1", port=80, timeout=0.2, demo_mode=False)
        hw_status = hw_client.fetch_status()
        results["15. ESP32 offline mode does not crash"] = (hw_status.get("online") is False and "offline" in hw_status.get("message").lower(), f"Resilient response: {hw_status.get('message')}")
    except Exception as e:
        results["15. ESP32 offline mode does not crash"] = (False, str(e))

    print("\n================== VERIFICATION SUMMARY ==================")
    all_passed = True
    for item, (passed, detail) in results.items():
        status_str = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{status_str}] {item}: {detail}")
    print("==========================================================")
    print(f"ALL 15 VERIFICATIONS PASSED: {all_passed}")

if __name__ == "__main__":
    run_verifications()
