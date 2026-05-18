# PulseReady

PulseReady is a real-time wearable health and performance monitoring platform that collects biometric data from an Apple Watch, processes it into actionable readiness insights, and visualizes unit-level health trends through an interactive web dashboard.

The project was designed to explore how wearable devices, live telemetry, and analytics can support performance monitoring in high-intensity or mission-focused environments. PulseReady transforms raw physiological signals into meaningful indicators such as fatigue, recovery, and an overall Mission Readiness Score (MRS), enabling faster and more informed decisions.

## Features

- Real-time biometric data collection from Apple Watch using HealthKit
- Live heart rate streaming during active workout sessions
- Backend APIs for ingesting raw and derived health metrics
- Mission Readiness Score (MRS) calculation based on weighted health factors
- Interactive admin dashboard for live monitoring and trend visualization
- Unit-level readiness tracking for multiple users
- Configurable weighting system for fatigue, recovery, heat, altitude, and sleep
- Secure authentication for dashboard access
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

## How It Works

1. The Apple Watch collects live biometric data, primarily heart rate, during an active workout session.
2. The iOS/Watch app streams raw readings to the backend.
3. The backend stores incoming data and computes derived performance metrics.
4. A Mission Readiness Score is generated using weighted physiological and environmental factors.
5. The admin dashboard displays live data streams, readiness scores, and user-level performance breakdowns.

## Mission Readiness Score

PulseReady uses a weighted scoring model to estimate readiness based on multiple factors, including:

- Fatigue
- Recovery
- Heat stress
- Altitude impact
- Sleep quality

These weights can be adjusted through the dashboard, making the platform flexible for different operational or training scenarios.

## Use Cases

PulseReady can be adapted for:

- Athlete performance monitoring
- Military or tactical readiness tracking
- First responder wellness monitoring
- Team-based health analytics
- Research projects involving wearable telemetry and live dashboards

## Project Goals

The main goals of this project were to:

- Build an end-to-end real-time health monitoring system
- Integrate wearable sensor data with cloud-connected applications
- Design a scalable telemetry pipeline for live analytics
- Convert raw biometric streams into decision-support metrics
- Create an intuitive dashboard for monitoring individual and team readiness

## Future Improvements

- Add more biometric signals such as SpO2, temperature, and HRV
- Improve the Mission Readiness Score with more advanced modeling
- Support historical analytics and long-term trend forecasting
- Add anomaly detection and alerting for high-risk conditions
- Deploy the system to a cloud environment for broader access
- Expand support for Android or additional wearable devices

## Why This Project Matters

PulseReady demonstrates how wearable computing, real-time backend systems, and interactive analytics can work together to create meaningful health intelligence. Rather than simply displaying raw sensor values, the platform focuses on translating data into readiness insights that users can act on.
