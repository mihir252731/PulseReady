# PulseReady

PulseReady is a real-time wearable health and performance monitoring platform that collects biometric data from an Apple Watch, processes it into actionable readiness insights, and visualizes individual and unit-level trends through a live web dashboard.

The project explores how wearable devices, live telemetry, and analytics can be combined to support decision-making in high-performance environments. Instead of only showing raw sensor values, PulseReady translates incoming health data into readable indicators such as fatigue, recovery, and an overall Mission Readiness Score (MRS).

## Features

- Real-time heart rate streaming from Apple Watch using HealthKit
- SwiftUI-based wearable client for live workout monitoring
- FastAPI backend for telemetry ingestion and analytics
- Mission Readiness Score (MRS) calculation from weighted health factors
- Next.js dashboard for live visualization of readiness and heart rate
- Unit-level monitoring for multiple users
- Adjustable score weights for fatigue, recovery, heat, altitude, and sleep
- JWT-based dashboard authentication
- WebSocket and polling support for near real-time updates

## Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- Chart.js

### Backend
- FastAPI
- Python
- SQLite
- WebSockets
- JWT Authentication

### Mobile / Wearable
- Swift
- SwiftUI
- HealthKit
- Apple Watch

## Project Structure

```text
PulseReady_GitHub/
├── HPPM_iOS_App/         # Apple Watch / iOS app source
├── server_fastapi/       # FastAPI backend
├── web-admin-next/       # Next.js dashboard
├── device_simulator.py   # Simulates telemetry for local testing
└── HPPMS.postman_collection.json
```

## How It Works

1. The Apple Watch app collects live heart-rate data during an active workout.
2. The wearable client sends raw biometric data to the backend.
3. The backend stores telemetry and computes derived metrics.
4. A Mission Readiness Score is generated using weighted performance factors.
5. The web dashboard displays live heart-rate streams, readiness scores, and metric breakdowns.

## Local Setup

### 1. Start the backend

```bash
cd server_fastapi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2. Start the dashboard

```bash
cd web-admin-next
npm install
npm run dev
```

### 3. Optional: run the telemetry simulator

```bash
python device_simulator.py
```

### 4. Run the Apple Watch app

Open `HPPM_iOS_App/HPPM2.xcodeproj` in Xcode and run the project on a paired iPhone + Apple Watch target.

## Environment Variables

### Backend

Create `server_fastapi/.env` from `.env.example` and configure values such as:

- `TEAM_KEY`
- `ADMIN_USER`
- `ADMIN_PASS`
- `JWT_SECRET`
- `DB_PATH`

### Frontend

Create `web-admin-next/.env.local` from `.env.example` and configure:

- `NEXT_PUBLIC_API_BASE`
- `NEXT_PUBLIC_WS_BASE`

## Use Cases

- Athlete performance monitoring
- Team-based health analytics
- Readiness tracking for high-intensity environments
- Wearable telemetry research projects
- Live physiological dashboard prototypes

## Future Improvements

- Add more biometric inputs such as SpO2, HRV, and body temperature
- Improve the Mission Readiness Score using stronger modeling and validation
- Add alerts for abnormal trends or readiness drops
- Store and analyze long-term history for trend forecasting
- Deploy the stack to a cloud environment
- Expand support for additional wearable devices

## Notes

This folder is a cleaned GitHub-ready version of the project. Large generated folders, local databases, dependency directories, and archive files were intentionally excluded to keep the repository lightweight and easier to publish.
