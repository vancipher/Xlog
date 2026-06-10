# camera_server.py
# Camera server for XLog - runs on laptop

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import cv2
import numpy as np
import threading
import time
from datetime import datetime

# Import your face recognition functions
from utils import get_embedding, cosine_similarity, mp_face_mesh
from models import load_all_students

app = Flask(__name__)
CORS(app)

# Global state
camera = None
camera_lock = threading.Lock()
recognition_active = False
students_db = {}
last_recognized = {}
cooldown = {}

XLOG_PI_URL = "http://192.168.0.50/api/face_verify"

def get_camera():
    """Get or initialize camera."""
    global camera
    with camera_lock:
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(0)
            camera. set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return camera

def release_camera():
    """Release camera."""
    global camera
    with camera_lock:
        if camera is not None:
            camera. release()
            camera = None

def generate_frames():
    """Generate camera frames with overlay."""
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    
    while True: 
        cam = get_camera()
        if not cam or not cam.isOpened():
            break
        
        success, frame = cam.read()
        if not success:
            break
        
        # Add overlay
        if recognition_active:
            cv2.putText(frame, "Recognition Active", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if last_recognized:
                cv2.putText(frame, f"Last: {last_recognized. get('name', '')}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(frame, "Waiting.. .", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)
    
    face_mesh.close()

def recognition_loop():
    """Background face recognition."""
    global recognition_active, students_db, last_recognized, cooldown
    
    SIMILARITY_THRESHOLD = 0.90
    COOLDOWN_SEC = 30
    
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    
    student_ids = list(students_db.keys())
    student_names = [students_db[sid]["name"] for sid in student_ids]
    embeddings = [students_db[sid]["embedding"] for sid in student_ids]
    
    print(f"[Recognition] Loaded {len(student_ids)} students")
    
    while recognition_active:
        cam = get_camera()
        if not cam or not cam.isOpened():
            break
        
        ret, frame = cam.read()
        if not ret:
            time.sleep(0.1)
            continue
        
        emb = get_embedding(frame, face_mesh=face_mesh)
        if emb is not None:
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
                last_time = cooldown.get(recognized_id, 0)
                
                if now - last_time >= COOLDOWN_SEC:
                    # Send to XLog Pi
                    try:
                        import requests
                        response = requests.post(
                            XLOG_PI_URL,
                            json={'student_id': recognized_id, 'student_name': recognized_name},
                            timeout=3
                        )
                        if response.ok:
                            data = response.json()
                            if data.get('success'):
                                status = data.get('status')
                                if status == 'completed':
                                    print(f"✅ VERIFIED: {recognized_name} (Card+Face)")
                                elif status == 'waiting_card': 
                                    print(f"⏳ Face verified:  {recognized_name} - waiting for card")
                                
                                last_recognized = {
                                    'id': recognized_id,
                                    'name': recognized_name,
                                    'time': datetime.now().strftime("%H:%M:%S"),
                                    'status': status
                                }
                                cooldown[recognized_id] = now
                    except Exception as e:
                        print(f"[Error] {e}")
        
        time.sleep(0.1)
    
    face_mesh.close()

@app.route('/camera/stream')
def camera_stream():
    """Video stream endpoint."""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/status')
def camera_status():
    """Check camera status."""
    cam = get_camera()
    return jsonify({
        'available': cam is not None and cam.isOpened(),
        'active': recognition_active
    })

@app.route('/recognition/start', methods=['POST'])
def start_recognition():
    """Start face recognition."""
    global recognition_active, students_db
    
    # Load students from database
    students_db = load_all_students()
    
    if not students_db:
        return jsonify({'success': False, 'error': 'No students in database'}), 400
    
    recognition_active = True
    
    # Start background thread
    thread = threading.Thread(target=recognition_loop, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Recognition started',
        'students_count': len(students_db)
    })

@app.route('/recognition/stop', methods=['POST'])
def stop_recognition():
    """Stop face recognition."""
    global recognition_active
    recognition_active = False
    return jsonify({'success': True, 'message':  'Recognition stopped'})

@app.route('/recognition/status')
def recognition_status():
    """Get recognition status."""
    return jsonify({
        'active': recognition_active,
        'last_recognized': last_recognized
    })

@app.route('/health')
def health():
    """Health check."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__': 
    print("=" * 50)
    print("XLog Camera Server")
    print("=" * 50)
    print("Starting on http://0.0.0.0:5000")
    print("Connect to WiFi:  CipherIsHere")
    print("Access from iPad: http://<laptop-ip>:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)