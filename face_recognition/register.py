# register.py
# Capture 5 embeddings for a student and save averaged embedding to database
# Usage: python register.py
# Compatible with Python 3.10

import cv2
import time
from typing import List, Optional
import numpy as np

from utils import get_embedding, mp_face_mesh
from models import save_student, init_database


def capture_embeddings(count: int = 5, wait_sec: float = 0.6) -> List[List[float]]:
    """
    Open webcam and capture `count` embeddings whenever a face is detected.
    Returns list of embeddings (each is list of floats). Blocks until enough captured or user cancels with 'q'.
    """
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return []

    embeddings: List[List[float]] = []
    print("Position the student's face in front of the camera.")
    print("Press 'q' to cancel.")

    # Create a FaceMesh instance and reuse for faster performance
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    last_capture_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read from webcam.")
                break

            display = frame.copy()
            # show capture count
            cv2.putText(display, f"Captured: {len(embeddings)}/{count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            cv2.imshow("Register - Press 'q' to quit", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            # Try to get embedding (fast)
            emb = get_embedding(frame, face_mesh=face_mesh)
            if emb is not None:
                now = time.time()
                # small cooldown to avoid many near-duplicate captures
                if now - last_capture_time >= wait_sec:
                    embeddings.append(emb)
                    last_capture_time = now
                    print(f"Captured {len(embeddings)}/{count}")
            if len(embeddings) >= count:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_mesh.close()

    return embeddings


def average_embeddings(embs: List[List[float]]) -> Optional[List[float]]:
    if not embs:
        return None
    arr = np.array(embs, dtype=float)
    mean = arr.mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm == 0:
        return None
    mean /= norm
    return mean.tolist()


def main():
    # Ensure DB initialized
    init_database()

    student_id = input("Enter student ID: ").strip()
    if not student_id:
        print("ERROR: student ID cannot be empty.")
        return
    
    student_name = input("Enter student name: ").strip()
    if not student_name:
        print("ERROR: student name cannot be empty.")
        return

    print("Starting webcam to capture embeddings...")
    embs = capture_embeddings(count=5, wait_sec=0.6)
    if len(embs) < 5:
        print("ERROR: Not enough embeddings captured. Registration cancelled.")
        return

    avg = average_embeddings(embs)
    if avg is None:
        print("ERROR: Failed to compute average embedding.")
        return

    success = save_student(student_id, student_name, avg)
    if success:
        print(f"Saved student '{student_id}' ({student_name}) to database (embedding length {len(avg)}).")
    else:
        print("ERROR: Failed to save to database.")


if __name__ == "__main__":
    main()