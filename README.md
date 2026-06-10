# Xlog

**RFID attendance system for classrooms** — runs on **Raspberry Pi 3 + PN532 reader + USB WiFi antenna**. The Pi broadcasts a WiFi network; the teacher connects from a phone or tablet, opens the **web control panel**, starts a session, and students tap RFID cards to log attendance.

[![Author](https://img.shields.io/badge/Author-vancipher-blue?style=flat-square)](https://github.com/vancipher)
[![Team](https://img.shields.io/badge/Team-Cyber%20X-red?style=flat-square)](https://cyberxsec.me)

**Status:** Tested in a real classroom setup — works reliably for session control and card-based check-in.

---

## How it works (production)

```
Teacher phone/tablet ──WiFi──► Raspberry Pi (access point + antenna)
                                    │
                                    ├── Web UI (start/stop session, view roster)
                                    └── PN532 RFID ──► student card tap ──► attendance log
```

1. Pi boots with **USB WiFi adapter + antenna** and creates a local network for the classroom.
2. Teacher joins that WiFi and opens the **browser UI** (Flask app in `face_recognition/`).
3. From the UI: create/start an attendance session, monitor scans, export results.
4. Students scan registered **RFID cards/tags** on the PN532 — names are recorded automatically.

A **desktop Tkinter app** (`desktop_app.py`) is included for development and demos on PC without Pi hardware.

---

## Features

- Student registration (name, ID, major, phone, RFID UID)
- Web UI to **control sessions** and view live attendance
- PN532 RFID scanning on the Pi (SPI)
- Session history + **CSV export**
- Arabic-friendly desktop UI for offline demos
- Optional **face verification** module (`face_recognition/`) — card + face pairing

---

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi 3 | Host — RFID + WiFi AP + web server |
| PN532 (SPI) | Read student RFID cards |
| USB WiFi adapter + **antenna** | Classroom hotspot for teacher device |
| RFID cards/tags | One UID per student |
| (Optional) USB webcam | Face-verify add-on |

Hands-on work: **soldering** PN532 headers, wiring SPI, mounting the antenna, flashing the Pi image, enabling SPI in `raspi-config`.

---

## Quick start — desktop demo (no Pi)

```bash
pip install -r requirements.txt
python desktop_app.py
```

| Field | Default |
|---|---|
| Username | `admin` |
| Password | `xlog2024` |

`data/students.json` and `data/sessions.json` are created on first run.

---

## Quick start — Raspberry Pi (tested setup)

### 1. Hardware

- Wire PN532 to Pi SPI (SCK, MOSI, MISO, CS).
- Attach USB WiFi dongle with external antenna.
- Enable SPI: `sudo raspi-config` → Interface Options → SPI.

### 2. Software

```bash
pip install -r requirements.txt
pip install adafruit-circuitpython-pn532 adafruit-blinka
cd face_recognition && pip install -r requirements.txt
```

### 3. WiFi access point

Configure the Pi to run as a classroom hotspot (hostapd + dnsmasq or NetworkManager AP mode) so the teacher can connect. Exact SSID/password depend on your deployment.

### 4. Run services

```bash
# Core RFID logic (integrated with web app on Pi)
cd face_recognition
python app.py
```

Open the control panel in a browser on the teacher device: `http://<pi-ip>:5000`

From the UI: register students (or preload UIDs), **start a session**, begin RFID collection, export when done.

---

## Project structure

```
Xlog/
├── xlog_system.py          # RFID + JSON storage core
├── desktop_app.py          # Tkinter GUI for PC demos
├── face_recognition/       # Pi web UI + API + optional face verify
│   ├── app.py              # Flask server — teacher control panel
│   ├── static/             # Web UI (session control, dashboard)
│   └── xlog_client.py      # Card/face event bridge
├── data/
│   ├── students.example.json
│   └── sessions.example.json
└── requirements.txt
```

---

## Data format

See `data/*.example.json`. Students are keyed by RFID UID; sessions store timestamped attendance arrays.

---

## Author

**Abdullah Y. Habash** ([@vancipher](https://github.com/vancipher)) · Cyber X · NTU Mosul

---

## License

Educational use only. Deploy on networks and hardware you own or have permission to use.
