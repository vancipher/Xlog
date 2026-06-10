# models.py
# Database models and initialization for the attendance system
# Compatible with Python 3.10

import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
import json
import logging

from pi_client import send_to_pi

logger = logging.getLogger(__name__)

DB_PATH = "attendance_system.db"


def init_database() -> bool:
    """
    Initialize the SQLite database with students and attendance tables.
    Returns True if successful.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Students table with face embeddings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                face_embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table (new) and attendance schema migration
        _ensure_sessions_table(cur)
        _ensure_attendance_schema(conn, cur)

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR initializing database: {e}")
        return False


# ==================== SCHEMA HELPERS ====================

def _ensure_sessions_table(cur: sqlite3.Cursor) -> None:
    """Create sessions table if missing."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT,
            session_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_date, start_time, end_time)
        )
        """
    )


def _ensure_attendance_schema(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """Add session_id column and adjust uniqueness to allow multiple sessions per day."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'")
    table_exists = cur.fetchone() is not None

    if not table_exists:
        cur.execute(
            """
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT,
                time_out TEXT,
                session_id INTEGER,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                UNIQUE(student_id, date, session_id)
            )
            """
        )
        conn.commit()
        return

    cur.execute("PRAGMA table_info(attendance)")
    columns = {row[1] for row in cur.fetchall()}

    needs_rebuild = False
    has_session_id = "session_id" in columns

    if not has_session_id:
        # Older schema: no session_id column
        needs_rebuild = True
    else:
        # Check if unique constraint covers session_id; if not, rebuild
        cur.execute("PRAGMA index_list(attendance)")
        indexes = cur.fetchall()
        has_desired_unique = False
        for idx in indexes:
            if idx[2]:  # unique flag
                cur.execute(f"PRAGMA index_info({idx[1]})")
                cols = [r[2] for r in cur.fetchall()]
                if cols == ["student_id", "date", "session_id"]:
                    has_desired_unique = True
                    break
        if not has_desired_unique:
            needs_rebuild = True

    if needs_rebuild:
        cur.execute("ALTER TABLE attendance RENAME TO attendance_old")
        cur.execute(
            """
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT,
                time_out TEXT,
                session_id INTEGER,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                UNIQUE(student_id, date, session_id)
            )
            """
        )
        cur.execute(
            """
            INSERT INTO attendance (id, student_id, date, time_in, time_out, session_id)
            SELECT id, student_id, date, time_in, time_out, NULL FROM attendance_old
            """
        )
        cur.execute("DROP TABLE attendance_old")
        conn.commit()


# ==================== STUDENT OPERATIONS ====================

def save_student(student_id: str, name: str, embedding: List[float]) -> bool:
    """
    Insert or replace a student with their face embedding.
    """
    if not student_id or not name or not embedding:
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        emb_text = json.dumps(embedding, separators=(",", ":"))
        
        cur.execute(
            "REPLACE INTO students (id, name, face_embedding) VALUES (?, ?, ?)",
            (student_id, name, emb_text)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR saving student: {e}")
        return False


def get_student(student_id: str) -> Optional[Dict]:
    """
    Retrieve a student by ID.
    Returns dict with id, name, face_embedding (as list).
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT id, name, face_embedding FROM students WHERE id = ?", (student_id,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "face_embedding": json.loads(row[2])
            }
        return None
    except Exception as e:
        print(f"ERROR getting student: {e}")
        return None


def load_all_students() -> Dict[str, Dict]:
    """
    Load all students from database.
    Returns dict: { student_id: {"name": name, "embedding": embedding_list} }
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT id, name, face_embedding FROM students")
        rows = cur.fetchall()
        conn.close()
        
        result = {}
        for student_id, name, emb_text in rows:
            try:
                emb = json.loads(emb_text)
                if isinstance(emb, list):
                    result[student_id] = {
                        "name": name,
                        "embedding": [float(x) for x in emb]
                    }
            except Exception:
                continue
        
        return result
    except Exception as e:
        print(f"ERROR loading students: {e}")
        return {}


# ==================== ATTENDANCE OPERATIONS ====================

def record_attendance(student_id: str, student_name: str, session_id_override: Optional[int] = None) -> Tuple[bool, str]:
    """
    Record attendance for a student.
    - If no record exists for the current session (or legacy day): create with time_in
    - If record exists for the current session with no time_out: update time_out
    - session_id_override lets callers force a specific session (e.g., manual selection in UI)
    
    Returns (success: bool, message: str)
    """
    try:
        now = datetime.now()
        today = now.date().isoformat()  # YYYY-MM-DD
        current_time = now.strftime("%H:%M:%S")
        event_timestamp = now.isoformat()
        session = _get_session_by_id(session_id_override) if session_id_override is not None else get_active_session(now)
        session_id = session["id"] if session else None
        session_date = session["session_date"] if session else today
        
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Check if student exists in students table
        cur.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if not cur.fetchone():
            conn.close()
            return False, f"Student {student_id} not found in database"
        
        # Check if attendance record exists for this session (or legacy null-session)
        if session_id is not None:
            cur.execute(
                "SELECT id, time_in, time_out FROM attendance WHERE student_id = ? AND date = ? AND session_id = ?",
                (student_id, session_date, session_id)
            )
        else:
            cur.execute(
                "SELECT id, time_in, time_out FROM attendance WHERE student_id = ? AND date = ? AND session_id IS NULL",
                (student_id, session_date)
            )
        existing = cur.fetchone()
        
        if existing:
            if existing[2]:
                conn.close()
                if session:
                    return True, f"Attendance already completed for {student_name} in session '{session.get('session_name') or session_id}'"
                return True, f"Attendance already completed for {student_name}"

            # Update time_out
            cur.execute(
                "UPDATE attendance SET time_out = ? WHERE id = ?",
                (current_time, existing[0])
            )
            conn.commit()
            conn.close()
            _push_to_pi(student_id, student_name, event_timestamp)
            if session:
                return True, f"Updated time_out for {student_name} in session '{session.get('session_name') or session_id}'"
            return True, f"Updated time_out for {student_name}"
        else:
            # Insert new record with time_in
            cur.execute(
                "INSERT INTO attendance (student_id, date, time_in, session_id) VALUES (?, ?, ?, ?)",
                (student_id, session_date, current_time, session_id)
            )
            conn.commit()
            conn.close()
            _push_to_pi(student_id, student_name, event_timestamp)
            if session:
                return True, f"Recorded time_in for {student_name} in session '{session.get('session_name') or session_id}'"
            return True, f"Recorded time_in for {student_name}"
            
    except Exception as e:
        print(f"ERROR recording attendance: {e}")
        return False, f"Database error: {str(e)}"


def _push_to_pi(student_id: str, student_name: str, timestamp_iso: str) -> None:
    """Fire-and-forget sync to Raspberry Pi; never block local success."""
    try:
        success, status_code = send_to_pi(student_id, student_name, timestamp_iso)
        if success:
            logger.info("Synced to Pi for %s (%s) at %s", student_name, student_id, timestamp_iso)
        else:
            logger.warning("Pi sync failed for %s (%s) at %s (status=%s)", student_name, student_id, timestamp_iso, status_code)
    except Exception as exc:
        logger.error("Pi sync exception for %s (%s) at %s: %s", student_name, student_id, timestamp_iso, exc)


def get_today_attendance() -> List[Dict]:
    """
    Get all attendance records for today.
    Returns list of dicts with student info and attendance times.
    """
    try:
        today = date.today().isoformat()
        
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                a.id,
                a.student_id,
                s.name,
                a.date,
                a.time_in,
                a.time_out,
                a.session_id,
                sess.session_name,
                sess.start_time,
                sess.end_time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            LEFT JOIN sessions sess ON a.session_id = sess.id
            WHERE a.date = ?
            ORDER BY a.time_in DESC
        """, (today,))
        
        rows = cur.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "student_id": row[1],
                "student_name": row[2],
                "date": row[3],
                "time_in": row[4],
                "time_out": row[5] if row[5] else "Not checked out",
                "session_id": row[6],
                "session_name": row[7],
                "session_start": row[8],
                "session_end": row[9]
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR getting today's attendance: {e}")
        return []


def get_all_attendance(limit: int = 500) -> List[Dict]:
    """
    Get all attendance records (for admin viewing).
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                a.id,
                a.student_id,
                s.name,
                a.date,
                a.time_in,
                a.time_out,
                a.session_id,
                sess.session_name,
                sess.start_time,
                sess.end_time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            LEFT JOIN sessions sess ON a.session_id = sess.id
            ORDER BY a.date DESC, a.time_in DESC
            LIMIT ?
        """, (limit,))
        
        rows = cur.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "student_id": row[1],
                "student_name": row[2],
                "date": row[3],
                "time_in": row[4],
                "time_out": row[5] if row[5] else "Not checked out",
                "session_id": row[6],
                "session_name": row[7],
                "session_start": row[8],
                "session_end": row[9]
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR getting attendance: {e}")
        return []


# ==================== SESSION OPERATIONS ====================

def create_session(session_date: str, start_time: str, end_time: str, session_name: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
    """Create a lecture session (date format YYYY-MM-DD, times HH:MM)."""
    if not session_date or not start_time or not end_time:
        return False, "Missing session fields", None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (session_name, session_date, start_time, end_time) VALUES (?, ?, ?, ?)",
            (session_name, session_date, start_time, end_time)
        )
        session_id = cur.lastrowid
        conn.commit()
        conn.close()
        return True, "Session created", session_id
    except sqlite3.IntegrityError:
        return False, "Session already exists for that window", None
    except Exception as e:
        return False, f"Error creating session: {e}", None


def list_sessions(session_date: Optional[str] = None) -> List[Dict]:
    """List sessions, optionally filtered by date."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        if session_date:
            cur.execute(
                "SELECT id, session_name, session_date, start_time, end_time FROM sessions WHERE session_date = ? ORDER BY start_time",
                (session_date,)
            )
        else:
            cur.execute(
                "SELECT id, session_name, session_date, start_time, end_time FROM sessions ORDER BY session_date DESC, start_time"
            )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "session_name": r[1],
                "session_date": r[2],
                "start_time": r[3],
                "end_time": r[4],
            }
            for r in rows
        ]
    except Exception:
        return []


def get_active_session(now: datetime) -> Optional[Dict]:
    """Return the session that covers the current timestamp, if any."""
    try:
        session_date = now.date().isoformat()
        current_time = now.strftime("%H:%M")
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_name, session_date, start_time, end_time
            FROM sessions
            WHERE session_date = ? AND start_time <= ? AND end_time >= ?
            ORDER BY start_time LIMIT 1
            """,
            (session_date, current_time, current_time)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "session_name": row[1],
                "session_date": row[2],
                "start_time": row[3],
                "end_time": row[4],
            }
        return None
    except Exception:
        return None


def _get_session_by_id(session_id: Optional[int]) -> Optional[Dict]:
    """Fetch a session by id; returns None if not found."""
    if session_id is None:
        return None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, session_name, session_date, start_time, end_time FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "session_name": row[1],
                "session_date": row[2],
                "start_time": row[3],
                "end_time": row[4],
            }
        return None
    except Exception:
        return None
