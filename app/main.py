"""
ALINA Smart Fridge Application Entry Point.
Initializes FastAPI, SQLite Database, Background Sensor Polling,
and static frontend serving.
"""

import os
import sys
import threading
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure app package is in pythonpath
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import settings, logger
from app.database.database import init_db, SessionLocal
from app.database.repository import seed_demo_data
from app.iot.sensor_manager import SensorManager
from app.api.routes import router as api_router, set_sensor_manager

# Create FastAPI app
app = FastAPI(
    title="ALINA – AI Smart Fridge Voice Assistant",
    description="Food Expiry Management, Waste Reduction, and IoT Integration",
    version="2.0.0",
)

# Enable CORS for local web interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
sensor_manager = SensorManager(demo_mode=settings.DEMO_MODE)
set_sensor_manager(sensor_manager)

# Register API routes
app.include_router(api_router)

# Mount frontend static directory
FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Mount images directory for scan previews
IMAGES_DIR = PROJECT_ROOT / "images"
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


@app.get("/")
def serve_index():
    """Serves the smart fridge web dashboard."""
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


# ================= Background Sensor Polling Thread =================
_stop_polling = threading.Event()


def _sensor_polling_worker():
    """Background worker periodically polling sensor readings."""
    logger.info("Background sensor polling thread started.")
    while not _stop_polling.is_set():
        try:
            sensor_manager.poll_sensors()
        except Exception as e:
            logger.error("Error in sensor polling loop: %s", e)
        time.sleep(3.0)


@app.on_event("startup")
def on_startup():
    """Initializes database, demo data seeding, and sensor polling."""
    logger.info("Starting ALINA Smart Fridge Backend...")
    # 1. Initialize SQLite Database
    init_db()

    # 2. Seed initial points and demo foods
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    # 3. Start background sensor polling
    t = threading.Thread(target=_sensor_polling_worker, daemon=True)
    t.start()
    logger.info("ALINA system is online. Mode: %s", "DEMO/SIMULATION" if settings.DEMO_MODE else "REAL IOT")


@app.on_event("shutdown")
def on_shutdown():
    """Graceful shutdown handler."""
    logger.info("Shutting down ALINA Smart Fridge Backend...")
    _stop_polling.set()


def start():
    """Main CLI runner entry point."""
    print("=" * 60)
    print("      ALINA – AI SMART FRIDGE VOICE ASSISTANT")
    print(f"      Mode: {'DEMO / SIMULATION' if settings.DEMO_MODE else 'REAL IOT HARDWARE'}")
    print(f"      Dashboard: http://{settings.HOST}:{settings.PORT}")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info" if settings.DEBUG else "warning"
    )


if __name__ == "__main__":
    start()
