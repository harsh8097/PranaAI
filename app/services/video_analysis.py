import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from scipy.signal import butter, detrend, sosfiltfilt


MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_VIDEO_SECONDS = 60
MIN_VIDEO_SECONDS = 15
SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi"}


def assess_heart_rate_condition(bpm: int | float | None) -> dict:
    if bpm is None:
        return {
            "status": "UNKNOWN",
            "is_well": None,
            "condition_label": "No Pulse Detected",
            "tone": "neutral",
            "summary": "Signal quality was not sufficient to determine heart rate or patient condition.",
            "recommendation": "Ensure adequate, steady lighting and minimal movement.",
        }
    val = round(bpm)
    if val < 50:
        return {
            "status": "CRITICAL_LOW",
            "is_well": False,
            "condition_label": "Attention Required · Marked Bradycardia (<50 BPM)",
            "tone": "danger",
            "summary": f"Detected heart rate of {val} BPM is significantly below typical adult resting boundaries. In non-athletes, this suggests marked sinus bradycardia.",
            "recommendation": "If patient experiences dizziness, fainting, shortness of breath, or weakness, seek urgent medical attention.",
        }
    if 50 <= val < 60:
        return {
            "status": "LOW_RESTING",
            "is_well": True,
            "condition_label": "Low Normal / Mild Bradycardia (50–59 BPM)",
            "tone": "info",
            "summary": f"Heart rate of {val} BPM is slightly below the standard adult reference range (60–100 BPM). Frequently seen in well-trained individuals or during deep rest.",
            "recommendation": "Generally benign if asymptomatic. Monitor for lightheadedness or unusual fatigue.",
        }
    if 60 <= val <= 100:
        return {
            "status": "WELL_CONDITION",
            "is_well": True,
            "condition_label": "Patient in Well Condition · Normal Resting Heart Rate (60–100 BPM)",
            "tone": "success",
            "summary": f"Patient is in well condition. Heart rate of {val} BPM falls squarely within the healthy adult resting range (60–100 BPM) with stable rhythmic parameters.",
            "recommendation": "Vital signs appear normal. Maintain healthy hydration, regular physical activity, and balanced nutrition.",
        }
    if 100 < val <= 120:
        return {
            "status": "ELEVATED",
            "is_well": False,
            "condition_label": "Attention Required · Elevated Heart Rate (101–120 BPM)",
            "tone": "warning",
            "summary": f"Heart rate of {val} BPM is moderately elevated above resting boundaries (Tachycardia). Often triggered by stress, recent movement, caffeine, or mild dehydration.",
            "recommendation": "Rest quietly in a sitting position, breathe deeply, drink water, and re-check after 5–10 minutes.",
        }
    return {
        "status": "HIGH_TACHYCARDIA",
        "is_well": False,
        "condition_label": "Attention Required · Marked Tachycardia (>120 BPM)",
        "tone": "danger",
        "summary": f"Heart rate of {val} BPM indicates significant cardiac acceleration at rest. May signify elevated physiological distress or arrhythmia.",
        "recommendation": "Cease activity immediately. If accompanied by chest tightness, palpitations, or lightheadedness, consult a medical professional promptly.",
    }


class VideoAnalysisService:
    def analyze(self, file_storage) -> dict:
        if file_storage is None or not file_storage.filename:
            return self._error("NO_FILE", "Choose an MP4, MOV, or AVI video before starting analysis.")

        filename = Path(file_storage.filename).name
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return self._error("UNSUPPORTED_VIDEO", "Unsupported video format. Please upload a valid MP4, MOV, or AVI file.")

        data = file_storage.read(MAX_VIDEO_BYTES + 1)
        if not data:
            return self._error("EMPTY_VIDEO", "The selected video is empty.")
        if len(data) > MAX_VIDEO_BYTES:
            return self._error("VIDEO_TOO_LARGE", "Video exceeds the 100 MB upload limit.")
        if not self._matches_container(data, extension):
            return self._error("INVALID_VIDEO", "The file contents do not match a supported video format.")

        fd, temp_path = tempfile.mkstemp(prefix="pranascan-video-", suffix=extension)
        try:
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(data)
            return self._analyze_path(temp_path)
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def _analyze_path(self, path: str) -> dict:
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            return self._error("INVALID_VIDEO", "The video could not be decoded. Please try another recording.")

        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        if fps <= 0 or frame_count <= 0 or duration <= 0:
            capture.release()
            return self._error("INVALID_VIDEO", "The video has no readable frames or valid timing information.")
        if duration < MIN_VIDEO_SECONDS:
            capture.release()
            return self._error("VIDEO_TOO_SHORT", f"Use a video at least {MIN_VIDEO_SECONDS} seconds long for signal analysis.")
        if duration > MAX_VIDEO_SECONDS:
            capture.release()
            return self._error("VIDEO_TOO_LONG", f"Videos must be {MAX_VIDEO_SECONDS} seconds or shorter.")
        if fps < 10 or fps > 60:
            capture.release()
            return self._error("UNSUITABLE_VIDEO", "Video frame rate must be between 10 and 60 FPS.")

        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        face_detector = cv2.CascadeClassifier(str(cascade_path))
        if face_detector.empty():
            capture.release()
            return self._error("PROCESSING_ERROR", "Face detector could not be initialized.")

        green_means = []
        multiple_face_frames = 0
        face_frames = 0
        processed_frames = 0
        frame_index = 0
        decoded_frames = 0

        while processed_frames < 900:
            success, frame = capture.read()
            if not success:
                break
            frame_index += 1
            decoded_frames += 1
            if frame_index % max(1, round(fps / 15)) != 0:
                continue
            processed_frames += 1

            height, width = frame.shape[:2]
            scale = min(1.0, 640 / max(width, height))
            if scale < 1.0:
                frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            if len(faces) > 1:
                multiple_face_frames += 1
            if len(faces) == 0:
                continue

            x, y, face_width, face_height = max(faces, key=lambda face: face[2] * face[3])
            left = x + int(face_width * 0.25)
            right = x + int(face_width * 0.75)
            top = y + int(face_height * 0.12)
            bottom = y + int(face_height * 0.38)
            roi = frame[top:bottom, left:right]
            if roi.size == 0:
                continue

            green_means.append(float(np.mean(roi[:, :, 1])))
            face_frames += 1

        capture.release()

        if processed_frames == 0:
            return self._error("INVALID_VIDEO", "No video frames could be decoded.")
        if decoded_frames < frame_count * 0.8:
            return self._error("INVALID_VIDEO", "The video appears truncated or too many frames could not be decoded.")
        face_coverage = face_frames / processed_frames
        if multiple_face_frames / processed_frames > 0.1:
            return self._error("MULTIPLE_FACES", "More than one face was detected. Record with one person in view.")
        if face_coverage < 0.7:
            return self._quality_warning(duration, processed_frames, face_coverage, "A face was not visible clearly enough throughout the video.")
        if len(green_means) < 150:
            return self._quality_warning(duration, processed_frames, face_coverage, "Too few usable face-region samples were collected.")

        sample_rate = processed_frames / duration
        heart_rate = self._estimate_heart_rate(np.asarray(green_means, dtype=np.float64), sample_rate)
        if heart_rate is None:
            return self._quality_warning(duration, processed_frames, face_coverage, "The facial color signal was not strong enough for a reliable heart-rate estimate.")

        patient_condition = assess_heart_rate_condition(heart_rate)

        return {
            "accepted": True,
            "status": "ESTIMATE_AVAILABLE",
            "alert": "",
            "message": "Video processed. This experimental estimate is not a medical measurement.",
            "duration_seconds": round(duration, 1),
            "frames_processed": processed_frames,
            "face_coverage": round(face_coverage, 2),
            "heart_rate_bpm": heart_rate,
            "patient_condition": patient_condition,
            "signal_quality": "Usable for an experimental estimate",
            "warning": "rPPG is sensitive to lighting, motion, camera quality, and compression. Do not use this estimate for diagnosis.",
        }

    def _estimate_heart_rate(self, signal: np.ndarray, sample_rate: float):
        if sample_rate < 8 or len(signal) < 150:
            return None
        signal = detrend(signal)
        if not np.isfinite(signal).all() or float(np.std(signal)) < 0.05:
            return None

        low = 0.7 / (sample_rate / 2)
        high = 3.0 / (sample_rate / 2)
        if low <= 0 or high >= 1 or low >= high:
            return None
        filtered = sosfiltfilt(butter(3, [low, high], btype="bandpass", output="sos"), signal)
        if float(np.std(filtered)) < 0.03:
            return None

        window = np.hanning(len(filtered))
        spectrum = np.abs(np.fft.rfft(filtered * window))
        frequencies = np.fft.rfftfreq(len(filtered), d=1 / sample_rate)
        mask = (frequencies >= 0.7) & (frequencies <= 3.0)
        if not np.any(mask):
            return None
        band = spectrum[mask]
        peak_index = int(np.argmax(band))
        peak = float(band[peak_index])
        background = float(np.median(band))
        if background <= 0 or peak / background < 3.0:
            return None

        peak_hz = float(frequencies[mask][peak_index])
        bpm = round(peak_hz * 60)
        if bpm < 42 or bpm > 180:
            return None
        return bpm

    def _matches_container(self, data: bytes, extension: str) -> bool:
        if extension == ".avi":
            return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"AVI "
        if extension in {".mp4", ".mov"}:
            return len(data) >= 12 and data[4:8] == b"ftyp"
        return False

    def _quality_warning(self, duration: float, frames: int, face_coverage: float, reason: str) -> dict:
        return {
            "accepted": True,
            "status": "INSUFFICIENT_SIGNAL_QUALITY",
            "alert": "",
            "message": "Video decoded, but no reliable heart-rate estimate could be produced.",
            "duration_seconds": round(duration, 1),
            "frames_processed": frames,
            "face_coverage": round(face_coverage, 2),
            "heart_rate_bpm": None,
            "signal_quality": "Insufficient",
            "warning": reason + " Improve lighting, keep still, and keep one face visible.",
        }

    def _error(self, status: str, message: str) -> dict:
        return {
            "accepted": False,
            "status": status,
            "alert": message,
            "message": message,
            "heart_rate_bpm": None,
        }
