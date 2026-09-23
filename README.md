# ALINA – AI and IoT-Based Smart Fridge Voice Assistant
### *For Food Expiry Management and Food Waste Reduction*

ALINA is a modular, AI-powered smart refrigerator software system and voice assistant designed to help households track groceries, monitor real-time shelf life, prevent food waste through timely consumption reminders, suggest recipes prioritizing foods closest to expiry, and interface with IoT hardware (ESP32) or run in pure software demo simulation.

---

## 1. What is Alina?
Food waste is a major economic and ecological issue, often caused by groceries being forgotten in the back of refrigerators until they spoil. **ALINA** solves this by combining:
- **Intelligent dynamic expiry calculations** based on actual dates.
- **Webcam OCR scanning** to capture expiry dates directly from food packaging.
- **Voice interaction & speech synthesis** powered by an intent-matching NLP engine.
- **Gamification points** rewarding users when food is eaten before expiry (+10 pts) and penalizing food wasted (-10 pts).
- **Dual-mode IoT integration**:
  - **Demo/Simulation Mode**: Runs on any laptop without hardware; simulates sensors, scale load-cell changes, and door alarms.
  - **Real IoT Mode**: Communicates over Wi-Fi with an ESP32 microcontroller reading DS18B20 temperature, reed switch door state, HX711 load cell weight, and controlling status LEDs, buzzers, and servo latches.

---

## 2. Key Features
- **Dynamic Expiry Engine**: Automatically computes `days_remaining = expiry_date - today` and assigns urgency badges (`CRITICAL`, `HIGH`, `MEDIUM`, `NORMAL`, `EXPIRED`).
- **Webcam Label OCR**: Captures food packaging via laptop webcam, runs OpenCV thresholding + Tesseract OCR, detects foods from a recognized dictionary, and allows human review before saving.
- **Voice & Chat Assistant**: Responds naturally to questions like *"What expires soon?"*, *"What should I cook today?"*, *"How much milk do I have?"*, and *"Is the door open?"*.
- **Expiry-Driven Recipe Recommendations**: Suggests recipes for foods expiring soonest (e.g., *Chicken rice* for chicken expiring tomorrow).
- **Gamification & Habit Building**: Tracks sustainability scores in SQLite (`data/alina.db`), awarding points for eating food on time.
- **Smart Door Alarm**: Detects if the fridge door has been left open longer than 15 seconds, alerting via visual UI, buzzer, and speech.
- **Consumption Detection**: Detects weight loss from the scale load cell and asks: *"Did you use the Chicken? (400g reduction)"* to confirm and reward points.
- **Fail-Safe & Graceful**: Never crashes if ESP32, microphone, webcam, or OCR binaries are missing.

---

## 3. System Architecture

```
smart_fridge_demo/
├── app/
│   ├── main.py                     # FastAPI entry point & background polling
│   ├── config/settings.py          # Configuration and centralized logging
│   ├── database/                   # SQLite database engine, models, and repository
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── food/                       # Food inventory, dynamic expiry, & consumption
│   │   ├── inventory.py
│   │   ├── expiry.py
│   │   ├── food_detection.py
│   │   └── consumption.py
│   ├── vision/                     # OpenCV camera, Tesseract OCR, date parsing
│   │   ├── camera.py
│   │   ├── ocr.py
│   │   └── expiry_parser.py
│   ├── voice/                      # SAPI5 / PowerShell TTS, STT, command router
│   │   ├── listener.py
│   │   ├── speaker.py
│   │   └── commands.py
│   ├── ai/                         # Recipe DB, recommendations, local AI coordinator
│   │   ├── assistant.py
│   │   ├── recipes.py
│   │   ├── recommendations.py
│   │   └── llm.py
│   ├── iot/                        # ESP32 Wi-Fi HTTP client, sensor manager, actuators
│   │   ├── esp32_client.py
│   │   ├── sensor_manager.py
│   │   ├── temperature.py
│   │   ├── door.py
│   │   ├── weight.py
│   │   └── actuators.py
│   ├── gamification/points.py      # Points scoring & waste penalties
│   └── api/                        # FastAPI REST routes and Pydantic schemas
│       ├── routes.py
│       └── schemas.py
├── frontend/                       # Modern appliance web dashboard
│   ├── index.html
│   ├── style.css
│   └── app.js
├── esp32/alina_esp32.ino           # Arduino firmware sketch for ESP32
├── data/alina.db                   # Local SQLite database (auto-seeded)
├── images/                         # Saved camera scans
├── tests/                          # Automated Pytest suite
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
├── run_alina.bat                   # 1-Click Windows launcher
└── README.md
```

---

## 4. Hardware Specifications (Real IoT Mode)
When running with physical hardware, connect the following components:

| Component | Function | ESP32 GPIO Pin | Voltage |
|---|---|---|---|
| **ESP32 NodeMCU** | Wi-Fi microcontroller | - | 5V USB |
| **DS18B20** | Waterproof temperature sensor | `GPIO 4` (with 4.7kΩ pullup to 3.3V) | 3.3V / 5V |
| **Reed Switch** | Magnetic door sensor | `GPIO 15` (to GND, internal pullup) | 3.3V |
| **HX711 Module** | Load cell scale amplifier | DT: `GPIO 16`, SCK: `GPIO 17` | 5V |
| **Active Buzzer** | Audio door/expiry alarm | `GPIO 18` | 3.3V / 5V |
| **Green LED** | Normal preservation status | `GPIO 19` (with 220Ω resistor) | 3.3V |
| **Yellow LED** | Warning status | `GPIO 21` (with 220Ω resistor) | 3.3V |
| **Red LED** | Critical / Spoilage warning | `GPIO 22` (with 220Ω resistor) | 3.3V |
| **Servo Motor (SG90)**| Automated door latch demo | `GPIO 13` | 5V |
| **5V Relay Module** | Low-voltage DC demonstration load | `GPIO 23` | 5V |

> [!CAUTION]
> **SAFETY WARNING**: The relay module is strictly for safe low-voltage demonstration loads (e.g., 5V/12V DC fans or demonstration lights). **NEVER connect 230V AC mains power to the system.**

---

## 5. Software Requirements
- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.13 (or 3.10+)
- **Web Browser**: Chrome, Edge, or Firefox

---

## 6. Installation Guide (Windows)

### Step 1: Clone or Open Workspace
Open PowerShell in the project directory:
```powershell
cd C:\Users\sanju\OneDrive\Documents\fridge\smart_fridge_demo
```

### Step 2: (Optional) Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 7. Environment Configuration (.env)
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Default `.env` settings:
```ini
# Operating mode (true = simulation without hardware; false = real ESP32 IoT)
DEMO_MODE=true

# ESP32 settings (when DEMO_MODE=false)
ESP32_IP=192.168.1.100
ESP32_PORT=80
ESP32_TIMEOUT=3.0

# Vision & OCR
CAMERA_INDEX=0
OCR_ENABLED=true
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Voice & Speech
VOICE_ENABLED=true
VOICE_RATE=160
VOICE_VOLUME=1.0

# Optional External AI (none | gemini | openai)
AI_PROVIDER=none
AI_API_KEY=

# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true
```

---

## 8. How to Run ALINA

### Method 1: Using the 1-Click Batch File (Recommended)
Double-click `run_alina.bat` or run:
```cmd
run_alina.bat
```
This activates your environment, starts the server, and automatically opens `http://127.0.0.1:8000` in your default browser.

### Method 2: Command Line
```powershell
python -m app.main
```
Navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

---

## 9. Operating Modes Explained

### Mode A: DEMO / SIMULATION MODE (`DEMO_MODE=true`)
- No microcontroller or circuit board required.
- Uses your laptop webcam, microphone, and speakers.
- Automatically generates realistic fridge sensor readings (3.8°C to 4.3°C, 60% humidity, 520g scale).
- Provides interactive simulation controls on the dashboard:
  - **Open Door**: Simulates door opening and triggers alarm after 15s.
  - **Simulate -400g**: Simulates food consumption from the scale and displays the confirmation prompt.
  - **Test Buzzer & Latch**: Exercises actuator triggers.

### Mode B: REAL IOT MODE (`DEMO_MODE=false`)
- Connects over local Wi-Fi to your ESP32 IP address.
- Polls live temperatures from the DS18B20 sensor.
- Reads real magnetic door closures and scale weight.
- Dispatches hardware commands (`BUZZER_ON`, `LED_CRITICAL`, `SERVO_OPEN`).
- **Resilience**: If the ESP32 disconnects, ALINA shows *"ESP32 offline – using last known data"* without crashing.

---

## 10. Voice Assistant Guide
ALINA accepts voice queries through the microphone or text input.
Common commands supported:
- *"What do we have in the fridge?"* or *"Show my food"*
- *"What expires soon?"*
- *"What expires today?"*
- *"What has expired?"*
- *"What should I cook today?"*
- *"What can I cook with chicken?"*
- *"How much milk do I have?"*
- *"What is the temperature?"*
- *"Is the fridge door open?"*
- *"How many points do I have?"*
- *"Mark chicken as consumed"*
- *"Exit Alina"*

TTS engine uses Windows SAPI5 (`pyttsx3`) with an automated fallback to PowerShell `System.Speech.Synthesis`.

---

## 11. Camera & OCR Expiry Detection
Click **[📷 Scan Food]** on the dashboard:
1. ALINA captures a frame from your webcam.
2. OpenCV enhances the image (Grayscale + Bilateral Filter + Otsu Binarization).
3. Tesseract extracts the text and parses date strings (`EXP 14/09/2026`, `Best Before 14/09/2026`, `2026-09-14`, etc.).
4. The system matches items to its recognized dictionary (*Chicken, Milk, Eggs, Cheese, Apple, Bread, Rice, Fish, etc.*).
5. **Human-in-the-Loop Confirmation**: The user can review and correct any values before clicking **[💾 SAVE TO FRIDGE]**.

*(If Tesseract-OCR is not installed, ALINA transparently flags OCR as unavailable and opens the manual entry form without errors).*

---

## 12. Gamification Rules
- **Initial Score**: `100 Points`
- **Consume food before expiry**: `+10 Points`
- **Act on reminder**: `+5 Points`
- **Food expires unused**: `-10 Points`
- **Unrecognized voice requests**: `0 Points` (No unfair penalty)

---

## 13. Running Automated Tests
Run pytest to verify the full test suite:
```powershell
python -m pytest tests/ -v
```
All 14 unit and integration tests covering expiry calculations, priority algorithms, date parsers, food CRUD, points, voice routing, IoT handling, and FastAPI endpoints will execute and pass.

---

## 14. Troubleshooting
1. **"No module named ..."**: Ensure you run `pip install -r requirements.txt` with your active Python environment.
2. **Camera shows unavailable**: Ensure your webcam is not locked by Zoom, Teams, or Windows Camera app.
3. **Microphone timeout**: If no audio is captured, you can always type commands directly into the **Ask Alina** chat box.
4. **Tesseract OCR not installed**: Download the Windows installer from [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki) and install to `C:\Program Files\Tesseract-OCR\`.

---

## 15. Future Improvements
- Multi-camera compartment viewing.
- Barcode/QR-code scanning support alongside OCR.
- Dynamic mobile notifications via Pushbullet/Telegram bot.
- Integration with local Ollama / small language models for recipe variations.
