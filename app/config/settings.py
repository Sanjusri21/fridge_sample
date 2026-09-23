"""
ALINA Smart Fridge Configuration & Settings
Loads settings from environment variables and .env file.
Sets up centralized logging for the application.
"""

import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root: /smart_fridge_demo
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
IMAGES_DIR = BASE_DIR / "images"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # Operating mode
    DEMO_MODE: bool = True

    # ESP32 settings
    ESP32_IP: str = "192.168.1.100"
    ESP32_PORT: int = 80
    ESP32_TIMEOUT: float = 3.0

    # Vision settings
    CAMERA_INDEX: int = 0
    OCR_ENABLED: bool = True
    TESSERACT_PATH: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Voice settings
    VOICE_ENABLED: bool = True
    VOICE_RATE: int = 160
    VOICE_VOLUME: float = 1.0

    # AI settings
    AI_PROVIDER: str = "none"  # "none", "gemini", "openai"
    AI_API_KEY: str = ""

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # Database settings
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'alina.db'}"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def setup_logging():
    """Sets up unified application logging to console and file."""
    log_file = LOGS_DIR / "alina.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger("ALINA")
    logger.info("Centralized logging initialized. Log file: %s", log_file)
    return logger


logger = setup_logging()
