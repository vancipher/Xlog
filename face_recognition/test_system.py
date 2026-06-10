# test_system.py
# Test script to verify the attendance system is working correctly
# Run this AFTER starting the Flask server

import requests
import json
from datetime import datetime

API_URL = "http://127.0.0.1:5000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """Test the health endpoint."""
    print_section("1. Testing Health Endpoint")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_post_attendance():
    """Test posting attendance."""
    print_section("2. Testing POST /attendance (Check-In)")
    
    test_data = {
        "student_id": "TEST_001",
        "student_name": "John Test Doe"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/attendance",
            json=test_data,
            timeout=5
        )
        print(f"Request Data: {json.dumps(test_data, indent=2)}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_get_today():
    """Test getting today's attendance."""
    print_section("3. Testing GET /attendance/today")
    
    try:
        response = requests.get(f"{API_URL}/attendance/today", timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("success") and data.get("count", 0) > 0:
            print(f"\n[+] Found {data['count']} attendance record(s) for today")
            return True
        else:
            print("\n[!] No attendance records found")
            return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def test_dashboard():
    """Test if dashboard is accessible."""
    print_section("4. Testing Dashboard")
    
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Content Type: {response.headers.get('Content-Type')}")
            print(f"Content Length: {len(response.text)} bytes")
            
            if "Face Recognition" in response.text:
                print("[+] Dashboard HTML contains expected content")
                return True
            else:
                print("[!] Dashboard HTML may be incomplete")
                return False
        else:
            print("[X] Dashboard not accessible")
            return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  FACE RECOGNITION ATTENDANCE SYSTEM - TEST SUITE".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    print(f"\nTesting API at: {API_URL}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    results = {
        "Health Check": test_health(),
        "POST Attendance": test_post_attendance(),
        "GET Today's Attendance": test_get_today(),
        "Dashboard Access": test_dashboard()
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "[+] PASS" if result else "[X] FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'=' * 60}")
    
    if passed == total:
        print("\n[*] All tests passed! System is working correctly.")
        print("\nNext steps:")
        print("  1. Open http://127.0.0.1:5000 in your browser")
        print("  2. Register students with: python register.py")
        print("  3. Start recognition with: python main.py")
    else:
        print("\n[!] Some tests failed. Please check:")
        print("  - Is the Flask server running? (python app.py)")
        print("  - Is the server accessible at http://127.0.0.1:5000?")
        print("  - Are all dependencies installed? (pip install -r requirements.txt)")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n[X] Unexpected error: {e}")

