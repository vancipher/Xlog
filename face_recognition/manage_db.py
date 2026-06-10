# manage_db.py
# Database management utility - Remove students, clear attendance, reset database
# Usage: python manage_db.py

import sqlite3
import os
from models import DB_PATH, init_database

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_all_students():
    """Display all registered students."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM students ORDER BY id")
        students = cur.fetchall()
        conn.close()
        
        if not students:
            print("\n[!] No students found in database.\n")
            return []
        
        print("\n" + "=" * 60)
        print("  REGISTERED STUDENTS")
        print("=" * 60)
        print(f"{'ID':<15} {'Name':<30} {'Registered':<15}")
        print("-" * 60)
        
        for student_id, name, created_at in students:
            created = created_at[:10] if created_at else "N/A"
            print(f"{student_id:<15} {name:<30} {created:<15}")
        
        print("=" * 60)
        print(f"Total: {len(students)} student(s)\n")
        
        return students
    except Exception as e:
        print(f"[X] Error reading database: {e}")
        return []

def delete_student_by_id(student_id):
    """Delete a specific student and their attendance records."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Check if student exists
        cur.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student = cur.fetchone()
        
        if not student:
            conn.close()
            print(f"[X] Student '{student_id}' not found.")
            return False
        
        student_name = student[0]
        
        # Delete attendance records
        cur.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        attendance_deleted = cur.rowcount
        
        # Delete student
        cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
        
        conn.commit()
        conn.close()
        
        print(f"[+] Deleted student '{student_name}' (ID: {student_id})")
        if attendance_deleted > 0:
            print(f"    Also deleted {attendance_deleted} attendance record(s)")
        
        return True
    except Exception as e:
        print(f"[X] Error deleting student: {e}")
        return False

def delete_all_students():
    """Delete all students and attendance records."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Count records
        cur.execute("SELECT COUNT(*) FROM students")
        student_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cur.fetchone()[0]
        
        if student_count == 0:
            conn.close()
            print("[!] Database is already empty.")
            return False
        
        # Delete all
        cur.execute("DELETE FROM attendance")
        cur.execute("DELETE FROM students")
        
        conn.commit()
        conn.close()
        
        print(f"[+] Deleted {student_count} student(s)")
        print(f"[+] Deleted {attendance_count} attendance record(s)")
        print("[+] Database cleared successfully!")
        
        return True
    except Exception as e:
        print(f"[X] Error clearing database: {e}")
        return False

def delete_all_attendance():
    """Delete all attendance records but keep students."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM attendance")
        count = cur.fetchone()[0]
        
        if count == 0:
            conn.close()
            print("[!] No attendance records found.")
            return False
        
        cur.execute("DELETE FROM attendance")
        conn.commit()
        conn.close()
        
        print(f"[+] Deleted {count} attendance record(s)")
        print("[+] Students remain in database")
        
        return True
    except Exception as e:
        print(f"[X] Error deleting attendance: {e}")
        return False

def reset_database():
    """Completely reset database - delete file and recreate tables."""
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"[+] Deleted database file: {DB_PATH}")
        
        init_database()
        print("[+] Created fresh database with empty tables")
        print("[+] Database reset complete!")
        
        return True
    except Exception as e:
        print(f"[X] Error resetting database: {e}")
        return False

def main_menu():
    """Display main menu and handle user input."""
    while True:
        clear_screen()
        print("\n" + "█" * 60)
        print("█" + " " * 58 + "█")
        print("█" + "  DATABASE MANAGEMENT UTILITY".center(58) + "█")
        print("█" + " " * 58 + "█")
        print("█" * 60)
        
        print("\n[*] MENU:")
        print("  1. View all students")
        print("  2. Delete specific student")
        print("  3. Delete all students (clear database)")
        print("  4. Delete all attendance records only")
        print("  5. Reset database (complete fresh start)")
        print("  0. Exit")
        
        choice = input("\n>> Enter your choice (0-5): ").strip()
        
        if choice == "0":
            print("\n[*] Goodbye!")
            break
        
        elif choice == "1":
            show_all_students()
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            students = show_all_students()
            if students:
                student_id = input("Enter student ID to delete (or press Enter to cancel): ").strip()
                if student_id:
                    confirm = input(f"[!] Delete student '{student_id}'? (yes/no): ").strip().lower()
                    if confirm == "yes":
                        delete_student_by_id(student_id)
                    else:
                        print("[X] Cancelled.")
                else:
                    print("[X] Cancelled.")
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            students = show_all_students()
            if students:
                confirm = input("[!] DELETE ALL STUDENTS? This cannot be undone! (yes/no): ").strip().lower()
                if confirm == "yes":
                    double_confirm = input("[!] Are you ABSOLUTELY sure? (yes/no): ").strip().lower()
                    if double_confirm == "yes":
                        delete_all_students()
                    else:
                        print("[X] Cancelled.")
                else:
                    print("[X] Cancelled.")
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            confirm = input("[!] Delete all attendance records? Students will remain. (yes/no): ").strip().lower()
            if confirm == "yes":
                delete_all_attendance()
            else:
                print("[X] Cancelled.")
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            print("\n[!] WARNING: This will DELETE the entire database file!")
            print("[!] All students and attendance records will be permanently lost!")
            confirm = input("\n[!] Type 'RESET' to confirm: ").strip()
            if confirm == "RESET":
                reset_database()
            else:
                print("[X] Cancelled.")
            input("\nPress Enter to continue...")
        
        else:
            print("[X] Invalid choice. Please enter 0-5.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        # Ensure database exists
        if not os.path.exists(DB_PATH):
            print(f"[!] Database not found. Creating new database...")
            init_database()
        
        main_menu()
    except KeyboardInterrupt:
        print("\n\n[*] Goodbye!")
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")
