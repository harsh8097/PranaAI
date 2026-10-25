# PranaScan AI Mobile Application

Cross-platform Flutter mobile application for **PranaScan AI Clinical Diagnostics & Physiological Telemetry Platform**.

---

## 📱 Features

1. **Dashboard & Telemetry HUD**: Live patient vitals overview (Heart Rate 72 BPM, SpO2 98%, NIBP 120/80 mmHg), privacy badges, and one-tap module launchers.
2. **Document Intake & OCR (Module 01)**: Verification of medical PDFs, smears, prescriptions, and radiology records with multi-stage authentication.
3. **Biochemical Lab Reader (Module 02)**: Multi-column biomarker extraction, biological reference interval comparison, outside-range highlight flags, and patient condition risk scoring.
4. **Grounded Clinical Copilot (Module 03)**: Doctor-patient dialogue assistant anchored strictly in the validated report findings without hallucinating values.
5. **Real-time Cardiac rPPG Telemetry (Module 04)**: Contactless facial ROI guide, 60 FPS oscilloscope trace using hardware-accelerated `EcgPainter`, dynamic heart rate counter with pulsing heart, and interactive cardiac rhythm simulators (Normal Sinus, Tachycardia, Bradycardia, Arrhythmia).

---

## 🚀 Running the App

### Prerequisites
- [Flutter SDK](https://flutter.dev/docs/get-started/install) (v3.0.0 or higher)
- Android Studio / Xcode or VS Code with Flutter extension
- Connected Android/iOS device or emulator

### Commands

1. **Install dependencies**:
   ```bash
   flutter pub get
   ```

2. **Run in development**:
   ```bash
   flutter run
   ```

3. **Build Android APK**:
   ```bash
   flutter build apk --release
   ```
   The generated APK will be located at `build/app/outputs/flutter-apk/app-release.apk`.

4. **Build iOS app**:
   ```bash
   flutter build ios --release
   ```

---

## 🌐 Backend Configuration

By default, the mobile app connects to the PranaScan production cloud backend:
```dart
static String baseUrl = 'https://pranaai8097.netlify.app';
```

To connect to your local Flask backend during development:
- **Android Emulator**: `http://10.0.2.2:5000`
- **iOS Simulator / Local Network**: `http://<YOUR_LAN_IP>:5000`

You can change this in [lib/services/api_service.dart](lib/services/api_service.dart). If the network is unreachable, the app seamlessly activates the in-app offline telemetry engine with zero interruption.
