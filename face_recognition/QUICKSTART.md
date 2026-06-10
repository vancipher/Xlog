# QUICK START GUIDE

## 🚀 Fast Installation (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Wait for installation to complete (may take 2-3 minutes).

### Step 2: Start the Server
```bash
python app.py
```

You should see:
```
==================================================
Face Recognition Attendance System
==================================================
Server starting on http://127.0.0.1:5000
...
```

**Keep this terminal open!**

### Step 3: Open Dashboard
Open your browser and go to:
```
http://127.0.0.1:5000
```

You should see the dark-themed dashboard with stats cards and an empty table.

---

## 👤 Register Your First Student

Open a **NEW terminal** (keep the server running):

```bash
python register.py
```

Follow the prompts:
1. Enter student ID: `TEST001`
2. Enter student name: `Test Student`
3. Face the camera
4. Wait for 5 captures (automatic)
5. Done!

---

## 📸 Test Face Recognition

Open **another NEW terminal**:

```bash
python main.py
```

When prompted:
- Press **Enter** to use localhost

The webcam window will open:
- Position your face in front of the camera
- When recognized, you'll see your name in green
- Console will show: `[HH:MM:SS] Sent attendance for Test Student (ID: TEST001) -> OK`

---

## 📊 Check the Dashboard

Go back to your browser (http://127.0.0.1:5000):
- You should see "1" in the "Present Today" card
- The table should show your attendance with time_in
- Status badge should say "Checked In"

**Test Check-Out:**
- Wait 30 seconds (cooldown period)
- Face the camera again
- Dashboard will update with time_out
- Status badge will change to "Checked Out"

---

## ✅ Success Checklist

- [ ] Dependencies installed without errors
- [ ] Flask server starts successfully
- [ ] Dashboard loads in browser
- [ ] Student registration completes
- [ ] Webcam opens for registration
- [ ] Face recognition detects and recognizes face
- [ ] Attendance POST succeeds (console shows "OK")
- [ ] Dashboard shows student in table
- [ ] time_in is recorded
- [ ] Second recognition updates time_out
- [ ] Stats cards update correctly
- [ ] Dashboard auto-refreshes every 10 seconds

---

## 🐛 Common Issues

### "Import errors" when running scripts
**Solution:** Install dependencies: `pip install -r requirements.txt`

### "Port 5000 already in use"
**Solution:** Stop the existing Flask process or change port in `app.py`:
```python
app.run(host='127.0.0.1', port=5001, debug=True)
```

### "No students found in database"
**Solution:** Register at least one student first: `python register.py`

### Webcam doesn't open
**Solution:** 
- Check camera is connected
- Close other apps using the camera
- Check Windows camera permissions

### Face not recognized
**Solution:**
- Ensure good lighting
- Look directly at the camera
- Try re-registering with better conditions

---

## 🎯 What Each File Does

| File | Purpose |
|------|---------|
| `app.py` | Flask web server and API |
| `models.py` | Database operations |
| `main.py` | Live face recognition |
| `register.py` | Register new students |
| `utils.py` | Face embedding utilities |
| `static/dashboard.html` | Web dashboard UI |
| `requirements.txt` | Python dependencies |
| `attendance_system.db` | SQLite database (auto-created) |

---

## 📝 Next Steps

1. **Register more students:** Run `register.py` multiple times
2. **Test with multiple people:** Each gets their own attendance record
3. **Check attendance history:** All records are saved in database
4. **Customize settings:** Edit threshold, cooldown, refresh rate (see SETUP_GUIDE.md)

---

## 🔥 Advanced Usage

### Export attendance to CSV
```bash
sqlite3 attendance_system.db
.headers on
.mode csv
.output attendance.csv
SELECT * FROM attendance;
.quit
```

### Use on Raspberry Pi
1. Change `app.py` host to `0.0.0.0`
2. Update `main.py` server URL to Pi's IP
3. Update `dashboard.html` API_BASE_URL

### Adjust recognition threshold
Edit `main.py`:
```python
SIMILARITY_THRESHOLD = 0.85  # Lower = more lenient (0.80-0.95 recommended)
```

---

## 📞 Support

If something doesn't work:
1. Check the error message in the terminal
2. Verify all dependencies are installed
3. Ensure Python 3.10 is being used
4. Check SETUP_GUIDE.md for detailed troubleshooting

---

**You're all set! 🎉**

The system is now ready to track attendance automatically using face recognition.
