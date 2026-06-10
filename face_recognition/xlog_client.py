# xlog_client.py
import requests

XLOG_PI_URL = "http://192.168.0.50/api/face_verify"

def send_face_verification(student_id, student_name):
    """Send face verification to XLog."""
    try:
        response = requests.post(
            XLOG_PI_URL,
            json={
                'student_id': student_id,
                'student_name': student_name
            },
            timeout=3
        )
        
        if response.ok:
            data = response.json()
            if data.get('success'):
                status = data.get('status')
                if status == 'completed':
                    print(f"✅ ATTENDANCE MARKED: {student_name} (Card+Face verified)")
                elif status == 'waiting_card':
                    print(f"⏳ Face verified for {student_name} - Waiting for card scan...")
                return True
            else:
                print(f"⚠️ {data.get('error', 'Unknown error')}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# For use in app.py
send_attendance_to_xlog = send_face_verification