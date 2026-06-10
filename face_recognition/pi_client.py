"""Lightweight client for pushing attendance events to the Raspberry Pi API."""
import logging
import os
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

PI_API_BASE = os.getenv("PI_API_BASE", "http://127.0.0.1:5000")
PI_ATTENDANCE_PATH = os.getenv("PI_ATTENDANCE_PATH", "/api/attendance")
PI_API_TIMEOUT = float(os.getenv("PI_API_TIMEOUT", "5"))


def _attendance_url() -> str:
    base = PI_API_BASE.rstrip("/")
    path = PI_ATTENDANCE_PATH if PI_ATTENDANCE_PATH.startswith("/") else f"/{PI_ATTENDANCE_PATH}"
    return f"{base}{path}"


def send_to_pi(student_id: str, student_name: str, timestamp: str, method: str = "face") -> Tuple[bool, Optional[int]]:
    """
    Push attendance to the Raspberry Pi API. Returns (success, status_code).
    The endpoint and timeout are configurable via environment variables:
    - PI_API_BASE (e.g., http://192.168.1.50:5000)
    - PI_ATTENDANCE_PATH (default /api/attendance)
    - PI_API_TIMEOUT (seconds, default 5)
    """
    url = _attendance_url()
    payload = {
        "student_id": student_id,
        "student_name": student_name,
        "timestamp": timestamp,
        "method": method,
    }
    try:
        resp = requests.post(url, json=payload, timeout=PI_API_TIMEOUT)
        if 200 <= resp.status_code < 300:
            logger.info("Pi sync ok (%s): %s %s at %s", resp.status_code, student_id, student_name, timestamp)
            return True, resp.status_code
        logger.warning(
            "Pi sync failed (%s): %s %s at %s - %s",
            resp.status_code,
            student_id,
            student_name,
            timestamp,
            resp.text[:200],
        )
        return False, resp.status_code
    except requests.RequestException as exc:
        logger.error("Pi sync error: %s", exc)
        return False, None
