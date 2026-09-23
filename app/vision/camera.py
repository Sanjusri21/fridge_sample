"""
Camera Manager for ALINA.
Accesses laptop webcam or external USB camera using OpenCV.
Handles unavailable devices gracefully.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import cv2

from app.config.settings import settings, IMAGES_DIR, logger


class CameraManager:
    def __init__(self, camera_index: Optional[int] = None):
        self.camera_index = camera_index if camera_index is not None else settings.CAMERA_INDEX

    def check_availability(self) -> Dict[str, Any]:
        """Tests if the camera device is accessible without keeping it open."""
        try:
            # On Windows, cv2.CAP_DSHOW provides fast camera initialization
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                # Fallback to default backend
                cap = cv2.VideoCapture(self.camera_index)

            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                if ret:
                    return {"available": True, "index": self.camera_index, "message": "Camera is available."}

            return {
                "available": False,
                "index": self.camera_index,
                "message": "Camera is unavailable or in use by another app."
            }
        except Exception as e:
            logger.warning("Camera check failed: %s", e)
            return {"available": False, "index": self.camera_index, "message": f"Camera error: {str(e)}"}

    def capture_frame(self, save: bool = True) -> Tuple[bool, Optional[str], Optional[Any]]:
        """
        Captures a single frame from webcam.
        Returns: (success: bool, saved_filepath: Optional[str], frame_ndarray: Optional[np.ndarray])
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index)

            if not cap.isOpened():
                logger.warning("Failed to open camera device index %s", self.camera_index)
                return False, None, None

            # Allow camera auto-exposure to settle
            for _ in range(5):
                ret, frame = cap.read()

            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                logger.warning("Failed to capture image frame from camera.")
                return False, None, None

            filepath = None
            if save:
                filename = f"scan_{int(time.time())}.jpg"
                file_dest = IMAGES_DIR / filename
                cv2.imwrite(str(file_dest), frame)
                filepath = str(file_dest)
                logger.info("Saved camera capture to %s", filepath)

            return True, filepath, frame

        except Exception as e:
            logger.error("Camera capture exception: %s", e)
            return False, None, None
