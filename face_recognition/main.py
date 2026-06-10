# main.py
# Live attendance: detect faces, recognize using stored embeddings, send POST to Flask server
# Usage: python main.py
# Compatible with Python 3.10

import cv2
import time
from typing import Dict, List, Optional
import requests

from utils import get_embedding, cosine_similarity, mp_face_mesh
from models import load_all_students, init_database

# Recognition config
SIMILARITY_THRESHOLD = 0.90  # per specification
SEND_COOLDOWN_SEC = 30       # seconds between repeated sends for same student


def send_attendance(server_url: str, student_id: str, student_name: str) -> bool:
    """
    Send POST request to Flask server attendance endpoint.
    Returns True if request succeeded (2xx).
    """
    url = f"{server_url}/attendance"
    try:
        resp = requests.post(
            url,
            json={
                "student_id": student_id,
                "student_name": student_name
            },
            timeout=5
        )
        return resp.status_code >= 200 and resp.status_code < 300
    except Exception as e:
        print(f"ERROR sending attendance: {e}")
        return False


def main():
    # Ensure DB initialized
    init_database()

    # Use localhost for development (change to Raspberry Pi IP if needed)
    server_url = input("Enter server URL (press Enter for http://127.0.0.1:5000): ").strip()
    if not server_url:
        server_url = "http://127.0.0.1:5000"
        print(f"Using default: {server_url}")

    # Load all students from database
    students_data = load_all_students()
    if not students_data:
        print("No students found in database. Please run register.py first.")
        return

    # Prepare for recognition
    student_ids = list(students_data.keys())
    student_names = [students_data[sid]["name"] for sid in student_ids]
    embeddings = [students_data[sid]["embedding"] for sid in student_ids]

    print(f"Loaded {len(student_ids)} students from database:")

    print(f"Loaded {len(student_ids)} students from database:")
    for sid, name in zip(student_ids, student_names):
        print(f"  - {sid}: {name}")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return

    # For performance, reuse single FaceMesh instance
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    last_sent: Dict[str, float] = {}  # student_id -> last sent timestamp

    print("Starting live attendance. Press 'q' to quit.")
    fps_time = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Failed to read from webcam.")
                break

            emb = get_embedding(frame, face_mesh=face_mesh)
            recognized_id: Optional[str] = None
            recognized_name: Optional[str] = None
            best_score = -1.0

            if emb is not None:
                # Compare with all stored embeddings
                for sid, name, db_emb in zip(student_ids, student_names, embeddings):
                    sim = cosine_similarity(emb, db_emb)
                    if sim > best_score:
                        best_score = sim
                        recognized_id = sid
                        recognized_name = name

                if best_score >= SIMILARITY_THRESHOLD and recognized_id is not None:
                    # Draw recognition on frame
                    cv2.putText(frame, f"{recognized_name} ({best_score:.2f})", (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

                    now = time.time()
                    last = last_sent.get(recognized_id, 0.0)
                    if now - last >= SEND_COOLDOWN_SEC:
                        success = send_attendance(server_url, recognized_id, recognized_name)
                        last_sent[recognized_id] = now
                        # small visual feedback to console
                        status = "OK" if success else "ERR"
                        print(f"[{time.strftime('%H:%M:%S')}] Sent attendance for {recognized_name} (ID: {recognized_id}) -> {status}")
                else:
                    # No match
                    cv2.putText(frame, "Unknown", (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "No face", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

            # Show FPS
            now = time.time()
            fps = 1.0 / (now - fps_time) if (now - fps_time) > 0 else 0.0
            fps_time = now
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.imshow("Live Attendance - press 'q' to quit", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_mesh.close()


if __name__ == "__main__":
    main()