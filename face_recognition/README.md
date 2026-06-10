# Lightweight Face-Recognition Attendance Prototype

This prototype implements a simple attendance system using:
- OpenCV (webcam capture)
- Mediapipe Face Mesh (468 landmarks)
- NumPy
- Requests (HTTP POST to Raspberry Pi)

Specs:
- Works on Windows 10/11 with Python 3.10
- Uses only: mediapipe, opencv-python, numpy, requests
- No dlib, no face_recognition, no heavy models

Files included:
- utils.py — helper functions (get_embedding, cosine_similarity, load_db, save_db)
- register.py — register a student by capturing 5 embeddings and saving average to faces.json
- main.py — live attendance mode; recognize, display name, and POST to Raspberry Pi
- faces.json — sample structure

Requirements (install once):
pip install mediapipe opencv-python numpy requests

How it works (high-level):
- Mediapipe Face Mesh extracts 468 3D landmarks (x,y,z) per detected face.
- We flatten the landmarks into a single embedding vector (468*3 = 1404).
- Embeddings are normalized (centered and L2 unitized).
- Cosine similarity between embeddings is used for recognition.
- If similarity > 0.90 → recognized, and an HTTP POST is sent to Raspberry Pi:
  POST http://<PI_IP>:5000/attendance
  JSON body: { "student_id": "<id>" }

Usage

1) Register a student
- Run:
  python register.py
- Enter student ID when prompted (e.g. `student_001`).
- Position the student's face in front of the webcam. The script captures 5 embeddings automatically when the face is detected (with a small cooldown to avoid duplicates).
- After capturing 5 samples, the script averages them and saves them to `faces.json` (overwrites any existing entry with same ID).

2) Run live attendance
- Run:
  python main.py
- Enter the Raspberry Pi IP address when prompted (e.g. `192.168.1.10`).
- A window will open showing camera feed, recognized name and FPS.
- When a student is recognized (cosine similarity > 0.90), the script will POST to:
  http://<PI_IP>:5000/attendance
  Body: { "student_id": "<id>" }
- To avoid spam, the same student's attendance is re-sent only after a cooldown (default 30 seconds).
- Press 'q' to quit.

Raspberry Pi side
- The Raspberry Pi should run an HTTP server listening on port 5000 and accept POST /attendance with JSON body {"student_id": "..."}.
- Example Flask endpoint (not provided here, since you said NFC registration is done separately on the Pi):
  @app.route('/attendance', methods=['POST'])
  def attendance():
      data = request.get_json()
      student_id = data.get('student_id')
      # store in Pi DB
      return jsonify({"ok": True})

Notes and tips
- Use good lighting and a simple background for higher accuracy.
- If recognition is too sensitive, you can increase SIMILARITY_THRESHOLD in main.py slightly (e.g. 0.92) or collect more stable registration samples.
- If webcam performance is slow, close other camera-using apps and reduce resolution in the scripts (CAP_PROP_FRAME_WIDTH/HEIGHT).
- The faces.json format is a map of student_id -> averaged embedding (list of floats).
- The scripts include error handling for camera and network issues.

If you want, I can:
- Provide a small Flask server example for the Raspberry Pi to receive and log attendance.
- Add confidence logging, or multi-face support.
- Add a CLI option to change the threshold or cooldown without editing code.

Enjoy — paste these files into a folder and run.