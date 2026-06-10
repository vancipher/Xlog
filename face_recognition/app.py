# app.py
# Flask backend for face recognition attendance system
# Compatible with Python 3.10

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from datetime import datetime
import os
import cv2
import numpy as np
import json
import subprocess
import threading
import time
import sqlite3
# Add this after line 15 (after other imports)
import sys
sys.path.append('.')
from xlog_client import send_attendance_to_xlog

from models import (
    init_database,
    record_attendance,
    get_today_attendance,
    get_all_attendance,
    DB_PATH,
    get_student,
    save_student,
    load_all_students,
    create_session,
    list_sessions
)

from utils import get_embedding, cosine_similarity, mp_face_mesh

app = Flask(__name__, static_folder='static', static_url_path='')

# Enable CORS for local development
CORS(app)

# Initialize database on startup
init_database()


@app.route('/')
def index():
    """Serve the main control panel HTML."""
    return send_from_directory('static', 'index.html')


@app.route('/dashboard')
def dashboard():
    """Serve the simple dashboard HTML."""
    return send_from_directory('static', 'dashboard.html')


@app.route('/attendance', methods=['POST'])
def post_attendance():
    """
    Endpoint to record attendance.
    
    Expected JSON:
    {
        "student_id": "ID_HERE",
        "student_name": "NAME_HERE"
    }
    
    Response:
    {
        "success": true/false,
        "message": "descriptive message",
        "timestamp": "current_time"
    }
    """
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON or empty body"
            }), 400
        
        
        student_id = data.get("student_id")
        student_name = data.get("student_name")
        session_id = data.get("session_id")
        
        if not student_id:
            return jsonify({
                "success": False,
                "error": "Missing student_id"
            }), 400
        
        if not student_name:
            return jsonify({
                "success": False,
                "error": "Missing student_name"
            }), 400
        
        # Record attendance (auto-detects time_in vs time_out)
        success, message = record_attendance(student_id, student_name, session_id_override=session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "student_id": student_id,
                "student_name": student_name
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": message
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/attendance/today', methods=['GET'])
def get_attendance_today():
    """
    Get all attendance records for today.
    
    Response:
    {
        "success": true,
        "date": "YYYY-MM-DD",
        "count": number,
        "records": [
            {
                "id": int,
                "student_id": str,
                "student_name": str,
                "date": str,
                "time_in": str,
                "time_out": str or "Not checked out"
            },
            ...
        ]
    }
    """
    try:
        records = get_today_attendance()
        
        return jsonify({
            "success": True,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "count": len(records),
            "records": records
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/attendance/all', methods=['GET'])
def get_attendance_all():
    """
    Get all attendance records (limited to last 500).
    
    Response: Same format as /attendance/today
    """
    try:
        limit = request.args.get('limit', 500, type=int)
        records = get_all_attendance(limit=limit)
        
        return jsonify({
            "success": True,
            "count": len(records),
            "records": records
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/student/<student_id>', methods=['GET'])
def get_student_info(student_id):
    """
    Get student information by ID.
    
    Response:
    {
        "success": true,
        "student": {
            "id": str,
            "name": str
        }
    }
    """
    try:
        student = get_student(student_id)
        
        if student:
            return jsonify({
                "success": True,
                "student": {
                    "id": student["id"],
                    "name": student["name"]
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Student not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200


@app.route('/sessions', methods=['GET'])
def list_sessions_route():
    """List lecture sessions; optional query param ?date=YYYY-MM-DD."""
    try:
        session_date = request.args.get('date')
        sessions = list_sessions(session_date)
        return jsonify({
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/sessions', methods=['POST'])
def create_session_route():
    """Create a lecture session (body: session_date YYYY-MM-DD, start_time HH:MM, end_time HH:MM, optional session_name)."""
    data = request.get_json(silent=True) or {}
    session_date = data.get('session_date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    session_name = data.get('session_name')

    success, message, session_id = create_session(session_date, start_time, end_time, session_name)
    status = 200 if success else 400
    return jsonify({
        "success": success,
        "message": message,
        "session_id": session_id
    }), status


# ==================== WEBCAM & REGISTRATION ENDPOINTS ====================

# Global variables for camera and registration state
camera = None
camera_lock = threading.Lock()
registration_state = {
    "active": False,
    "student_id": None,
    "student_name": None,
    "embeddings": [],
    "status": "idle",
    "message": ""
}
recognition_state = {
    "active": False,
    "last_recognized": {},
    "cooldown": {}
}

def get_camera():
    """Get or initialize camera."""
    global camera
    with camera_lock:
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return camera

def release_camera():
    """Release camera resource."""
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

def generate_camera_frames():
    """Generate camera frames for video streaming."""
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    
    while True:
        cam = get_camera()
        if cam is None or not cam.isOpened():
            break
            
        success, frame = cam.read()
        if not success:
            break
        
        # Add status overlay
        if registration_state["active"]:
            cv2.putText(frame, f"Capturing: {len(registration_state['embeddings'])}/5", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, registration_state["message"], 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if recognition_state["active"]:
            cv2.putText(frame, "Recognition Active", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if recognition_state["last_recognized"]:
                last = recognition_state["last_recognized"]
                cv2.putText(frame, f"Last: {last.get('name', 'Unknown')}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS

@app.route('/camera/stream')
def camera_stream():
    """Video streaming route."""
    return Response(generate_camera_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/status', methods=['GET'])
def camera_status():
    """Check camera availability."""
    try:
        cam = get_camera()
        if cam and cam.isOpened():
            return jsonify({"success": True, "available": True}), 200
        else:
            return jsonify({"success": True, "available": False}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/register/start', methods=['POST'])
def start_registration():
    """Start student registration process."""
    global registration_state
    
    data = request.get_json()
    student_id = data.get('student_id')
    student_name = data.get('student_name')
    
    if not student_id or not student_name:
        return jsonify({"success": False, "error": "Missing student_id or student_name"}), 400
    
    # Reset registration state
    registration_state = {
        "active": True,
        "student_id": student_id,
        "student_name": student_name,
        "embeddings": [],
        "status": "capturing",
        "message": "Position face in front of the camera"
    }
    
    # Start background capture thread
    thread = threading.Thread(target=capture_embeddings_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "Registration started",
        "student_id": student_id,
        "student_name": student_name
    }), 200

def capture_embeddings_background():
    """Background thread to capture face embeddings."""
    global registration_state
    
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    
    last_capture_time = 0
    wait_time = 0.6
    
    while registration_state["active"] and len(registration_state["embeddings"]) < 5:
        cam = get_camera()
        if not cam or not cam.isOpened():
            registration_state["status"] = "error"
            registration_state["message"] = "Camera not available"
            break
        
        ret, frame = cam.read()
        if not ret:
            continue
        
        now = time.time()
        if now - last_capture_time >= wait_time:
            emb = get_embedding(frame, face_mesh=face_mesh)
            if emb is not None:
                registration_state["embeddings"].append(emb)
                last_capture_time = now
                registration_state["message"] = f"Captured {len(registration_state['embeddings'])}/5"
                print(f"[Registration] Captured {len(registration_state['embeddings'])}/5")
        
        time.sleep(0.1)
    
    face_mesh.close()
    
    # Process captured embeddings
    if len(registration_state["embeddings"]) >= 5:
        try:
            # Average embeddings
            arr = np.array(registration_state["embeddings"], dtype=float)
            mean = arr.mean(axis=0)
            norm = np.linalg.norm(mean)
            if norm > 0:
                mean /= norm
                avg_embedding = mean.tolist()
                
                # Save to database
                success = save_student(
                    registration_state["student_id"],
                    registration_state["student_name"],
                    avg_embedding
                )
                
                if success:
                    registration_state["status"] = "completed"
                    registration_state["message"] = "Registration successful!"
                    print(f"[Registration] Successfully registered {registration_state['student_name']}")
                else:
                    registration_state["status"] = "error"
                    registration_state["message"] = "Failed to save to database"
            else:
                registration_state["status"] = "error"
                registration_state["message"] = "Invalid embeddings"
        except Exception as e:
            registration_state["status"] = "error"
            registration_state["message"] = f"Error: {str(e)}"
    else:
        registration_state["status"] = "error"
        registration_state["message"] = "Not enough embeddings captured"
    
    time.sleep(2)
    registration_state["active"] = False

@app.route('/register/status', methods=['GET'])
def registration_status():
    """Get registration status."""
    return jsonify({
        "success": True,
        "active": registration_state["active"],
        "status": registration_state["status"],
        "message": registration_state["message"],
        "captured": len(registration_state["embeddings"]),
        "total": 5
    }), 200

@app.route('/register/cancel', methods=['POST'])
def cancel_registration():
    """Cancel ongoing registration."""
    global registration_state
    registration_state["active"] = False
    registration_state["status"] = "cancelled"
    return jsonify({"success": True, "message": "Registration cancelled"}), 200

@app.route('/recognition/start', methods=['POST'])
def start_recognition():
    """Start live face recognition (optionally locked to a session)."""
    global recognition_state
    
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    
    # Load students from database
    students = load_all_students()
    if not students:
        return jsonify({"success": False, "error": "No students in database"}), 400
    
    recognition_state = {
        "active": True,
        "last_recognized": {},
        "cooldown": {},
        "students": students,
        "session_id": session_id,
    }
    
    # Start background recognition thread
    thread = threading.Thread(target=recognition_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "Recognition started",
        "students_count": len(students),
        "session_id": session_id
    }), 200

def recognition_background():
    """Background thread for face recognition."""
    global recognition_state
    
    SIMILARITY_THRESHOLD = 0.90
    COOLDOWN_SEC = 30
    
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    
    students = recognition_state["students"]
    forced_session_id = recognition_state.get("session_id")
    student_ids = list(students.keys())
    student_names = [students[sid]["name"] for sid in student_ids]
    embeddings = [students[sid]["embedding"] for sid in student_ids]
    try:
        while recognition_state["active"]:
            cam = get_camera()
            if not cam or not cam.isOpened():
                break
            
            ret, frame = cam.read()
            if not ret:
                continue
            
            emb = get_embedding(frame, face_mesh=face_mesh)
            if emb is None:
                time.sleep(0.1)
                continue
            
            best_score = -1.0
            recognized_id = None
            recognized_name = None
            
            for sid, name, db_emb in zip(student_ids, student_names, embeddings):
                sim = cosine_similarity(emb, db_emb)
                if sim > best_score:
                    best_score = sim
                    recognized_id = sid
                    recognized_name = name
            
            if best_score >= SIMILARITY_THRESHOLD and recognized_id:
                now = time.time()
                last_time = recognition_state["cooldown"].get(recognized_id, 0)
                
                if now - last_time >= COOLDOWN_SEC:
                    success, message = record_attendance(
                        recognized_id,
                        recognized_name,
                        session_id_override=forced_session_id
                    )
                    
                    if success:
                        recognition_state["last_recognized"] = {
                            "id": recognized_id,
                            "name": recognized_name,
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "message": message
                        }
                        recognition_state["cooldown"][recognized_id] = now
                        print(f"[Recognition] {message}")
                        
                        # Send attendance to XLog on Raspberry Pi
                        try:
                            xlog_success = send_attendance_to_xlog(recognized_id, recognized_name)
                            if xlog_success:
                                print(f"[XLog] ✅ Sent to Pi: {recognized_name}")
                            else:
                                print(f"[XLog] ⚠️ Failed to send to Pi (continuing locally)")
                        except Exception as exc:
                            print(f"[XLog] ❌ Error: {exc}")
                        
                        # Notify Pi to prompt card scan
                        try:
                            import requests
                            response = requests.post(
                                "http://192.168.0.50/api/face_detected",
                                json={'student_id': recognized_id, 'student_name': recognized_name},
                                timeout=3
                            )
                            if response.ok:
                                data = response.json()
                                if data.get('success'):
                                    print(f"[Pi] ✅ {data.get('message')} - SCAN CARD NOW")
                                else:
                                    print(f"[Pi] ⚠️ {data.get('error')}")
                        except Exception as exc:
                            print(f"[Pi] ❌ Cannot connect:  {exc}")
            
            time.sleep(0.1)
    finally:
        face_mesh.close()

@app.route('/recognition/status', methods=['GET'])
def recognition_status():
    """Get recognition status."""
    return jsonify({
        "success": True,
        "active": recognition_state["active"],
        "last_recognized": recognition_state["last_recognized"]
    }), 200

@app.route('/recognition/stop', methods=['POST'])
def stop_recognition():
    """Stop live recognition."""
    global recognition_state
    recognition_state["active"] = False
    return jsonify({"success": True, "message": "Recognition stopped"}), 200


# ==================== DATABASE MANAGEMENT ENDPOINTS ====================

@app.route('/db/students', methods=['GET'])
def get_all_students():
    """Get list of all registered students."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM students ORDER BY id")
        students = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return jsonify({
            "success": True,
            "students": students,
            "count": len(students)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/db/student/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a specific student and their attendance records."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Check if student exists
        cur.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student = cur.fetchone()
        
        if not student:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Student '{student_id}' not found"
            }), 404
        
        student_name = student[0]
        
        # Delete attendance records
        cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        attendance_deleted = cur.rowcount
        
        # Delete student
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Deleted student '{student_name}' (ID: {student_id})",
            "attendance_records_deleted": attendance_deleted
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/db/attendance/clear', methods=['DELETE'])
def clear_attendance_records():
    """Clear all attendance records (keep students)."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM attendance")
        count = cur.fetchone()[0]
        
        if count == 0:
            conn.close()
            return jsonify({
                "success": True,
                "message": "No attendance records to clear",
                "records_deleted": 0
            }), 200
        
        cur.execute("DELETE FROM attendance")
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Cleared {count} attendance record(s)",
            "records_deleted": count
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/db/reset', methods=['DELETE'])
def reset_database():
    """Delete all students and attendance records."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM students")
        student_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cur.fetchone()[0]
        
        cur.execute("DELETE FROM attendance")
        cur.execute("DELETE FROM students")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Database reset complete",
            "students_deleted": student_count,
            "attendance_deleted": attendance_count
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== SYSTEM TEST ENDPOINT ====================

@app.route('/test/system', methods=['GET'])
def test_system():
    """Run system tests and return results."""
    results = {
        "health": False,
        "database": False,
        "students_count": 0,
        "attendance_count": 0,
        "camera": False
    }
    
    try:
        # Test 1: Health check
        results["health"] = True
        
        # Test 2: Database connectivity
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM students")
        results["students_count"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM attendance")
        results["attendance_count"] = cur.fetchone()[0]
        
        results["database"] = True
        conn.close()
        
        # Test 3: Camera availability
        test_cam = cv2.VideoCapture(0)
        if test_cam.isOpened():
            results["camera"] = True
            test_cam.release()
        
        success = results["health"] and results["database"]
        
        return jsonify({
            "success": success,
            "results": results,
            "message": "System test complete" if success else "Some tests failed"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "results": results
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("=" * 50)
    print("Face Recognition Attendance System")
    print("=" * 50)
    print(f"Server starting on http://127.0.0.1:5000")
    print(f"Dashboard: http://127.0.0.1:5000/")
    print(f"API Endpoints:")
    print(f"  POST /attendance - Record attendance")
    print(f"  GET  /attendance/today - Get today's attendance")
    print(f"  GET  /attendance/all - Get all attendance records")
    print("=" * 50)
    
    # Run on localhost for development
    app.run(host='127.0.0.1', port=5000, debug=True)
