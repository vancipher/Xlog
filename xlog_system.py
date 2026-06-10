import json
import time
from datetime import datetime
import os

# For RFID - will work if hardware is available
try:
    import board
    import busio
    import digitalio
    from adafruit_pn532.spi import PN532_SPI
    RFID_AVAILABLE = True
except ImportError:
    RFID_AVAILABLE = False
    print("RFID hardware libraries not available. Running in simulation mode.")


class XLogSystem:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        self.students_file = os.path.join(self.data_dir, 'students.json')
        self.sessions_file = os.path.join(self.data_dir, 'sessions.json')
        self.current_session = None
        
        # Initialize RFID if available
        if RFID_AVAILABLE:
            try:
                self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
                self.cs_pin = digitalio.DigitalInOut(board.D8)
                self.pn532 = PN532_SPI(self.spi, self.cs_pin, debug=False)
                self.pn532.SAM_configuration()
                print("[XLog] PN532 Ready (SPI)")
            except Exception as e:
                print(f"[XLog] RFID initialization failed: {e}")
                self.pn532 = None
        else:
            self.pn532 = None
        
        self.load_data()
        print("[XLog] System initialized")

    def load_data(self):
        """Load students and sessions from JSON files"""
        try:
            with open(self.students_file, 'r', encoding='utf-8') as f:
                self.students = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.students = {}
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                self.sessions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.sessions = []

    def save_students(self):
        """Save students to JSON file"""
        with open(self.students_file, 'w', encoding='utf-8') as f:
            json.dump(self.students, f, ensure_ascii=False, indent=2)

    def save_sessions(self):
        """Save sessions to JSON file"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)

    def scan_card(self, timeout=2):
        """Scan RFID card and return UID"""
        if self.pn532:
            try:
                uid = self.pn532.read_passive_target(timeout=timeout)
                if uid:
                    return ''.join([f'{i:02X}' for i in uid])
            except Exception as e:
                print(f"[XLog] Scan error: {e}")
        return None

    def add_student(self, uid, name, student_id, major='', phone=''):
        """Add a new student to the system"""
        self.students[uid] = {
            'name': name,
            'student_id': student_id,
            'major': major,
            'phone': phone,
            'registered': datetime.now().isoformat()
        }
        self.save_students()
        return True

    def delete_student(self, uid):
        """Delete a student from the system"""
        if uid in self.students:
            del self.students[uid]
            self.save_students()
            return True
        return False

    def start_session(self, name):
        """Start a new attendance session"""
        self.current_session = {
            'name': name,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'attendance': []
        }
        return True

    def record_attendance(self, uid):
        """Record attendance for a student in current session"""
        if not self.current_session:
            return False
        
        if uid not in self.students:
            return False
        
        # Check if already recorded
        for att in self.current_session['attendance']:
            if att['uid'] == uid:
                return False
        
        student = self.students[uid]
        self.current_session['attendance'].append({
            'uid': uid,
            'name': student['name'],
            'student_id': student['student_id'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        return True

    def stop_session(self):
        """Stop current session and save it"""
        if self.current_session:
            self.sessions.append(self.current_session)
            self.save_sessions()
            session = self.current_session
            self.current_session = None
            return session
        return None

    def get_session_status(self):
        """Get current session status"""
        if self.current_session:
            return {'active': True, 'session': self.current_session}
        return {'active': False}
