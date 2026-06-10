# utils.py
# Helper functions for Mediapipe FaceMesh embedding, cosine similarity, and SQLite DB I/O
# Compatible with Python 3.10
from typing import Optional, Dict, List
import json
import sqlite3
import os
import numpy as np
import mediapipe as mp
import cv2

DB_PATH = "faces.db"

mp_face_mesh = mp.solutions.face_mesh


def get_embedding(frame: np.ndarray,
                  face_mesh: Optional[mp_face_mesh.FaceMesh] = None
                  ) -> Optional[List[float]]:
    """
    Given a BGR frame (numpy array), detect face landmarks using Mediapipe FaceMesh,
    return a normalized flattened embedding (list of floats) of size 468*3 = 1404.
    Returns None if no face is detected or on error.
    """
    try:
        if frame is None:
            return None

        # Use a local FaceMesh if not provided
        local = False
        if face_mesh is None:
            face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            local = True

        # Convert to RGB as mediapipe expects RGB input
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            if local:
                face_mesh.close()
            return None

        # Get first face landmarks (468 landmarks)
        landmarks = results.multi_face_landmarks[0].landmark

        # Collect x, y, z in normalized coordinates (relative)
        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)  # shape (468,3)

        # Normalize coordinates for scale/translation invariance:
        # 1) center by mean
        coords -= coords.mean(axis=0)

        # 2) flatten and divide by L2 norm to make vector unit length
        flat = coords.flatten()
        norm = np.linalg.norm(flat)
        if norm == 0:
            if local:
                face_mesh.close()
            return None
        embedding = (flat / norm).astype(float)

        if local:
            face_mesh.close()
        return embedding.tolist()

    except Exception:
        # On any error, return None
        return None


def cosine_similarity(vecA: List[float], vecB: List[float]) -> float:
    """
    Compute cosine similarity between two vectors (lists or numpy arrays).
    Returns similarity as float in [-1, 1]. Handles zero vectors defensively.
    """
    a = np.array(vecA, dtype=float)
    b = np.array(vecB, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return -1.0  # treat as totally dissimilar
    sim = float(np.dot(a, b) / (norm_a * norm_b))
    return sim


# ------------------- SQLite DB Helpers -------------------


def init_db(path: str = DB_PATH) -> bool:
    """
    Initialize SQLite DB file and create faces table if not exists.
    Table schema: faces(student_id TEXT PRIMARY KEY, embedding TEXT)
    embedding stored as JSON list of floats.
    """
    try:
        conn = sqlite3.connect(path, timeout=5)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS faces (student_id TEXT PRIMARY KEY, embedding TEXT NOT NULL)"
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def save_embedding(student_id: str, embedding: List[float], path: str = DB_PATH) -> bool:
    """
    Insert or replace embedding for student_id.
    Embedding is stored as JSON text.
    """
    if not student_id or not isinstance(embedding, list):
        return False
    try:
        # Ensure DB exists
        init_db(path)
        conn = sqlite3.connect(path, timeout=5)
        cur = conn.cursor()
        emb_text = json.dumps(embedding, separators=(",", ":"))
        cur.execute(
            "REPLACE INTO faces (student_id, embedding) VALUES (?, ?)",
            (student_id, emb_text),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def load_db(path: str = DB_PATH) -> Dict[str, List[float]]:
    """
    Load all embeddings from SQLite DB.
    Returns dict: { student_id: embedding_list }
    If DB doesn't exist or is invalid, returns empty dict.
    """
    if not os.path.exists(path):
        return {}
    try:
        conn = sqlite3.connect(path, timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT student_id, embedding FROM faces")
        rows = cur.fetchall()
        conn.close()
        result: Dict[str, List[float]] = {}
        for sid, emb_text in rows:
            try:
                emb = json.loads(emb_text)
                if isinstance(emb, list) and all(isinstance(x, (float, int)) for x in emb):
                    result[str(sid)] = [float(x) for x in emb]
            except Exception:
                continue
        return result
    except Exception:
        return {}