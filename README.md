# PranaScan AI

PranaScan AI is a Flask-based medical intelligence platform for validating medical documents, extracting OCR data, and preparing the foundation for physiological measurement and report interpretation workflows.

## Architecture

- Flask application factory in [app/__init__.py](app/__init__.py)
- Document validation service in [app/services/document_validation.py](app/services/document_validation.py)
- API routes in [app/routes.py](app/routes.py)
- Frontend in [templates/index.html](templates/index.html) and [static](static)

## Installation on Windows

1. Create a virtual environment:
   `py -3.13 -m venv .venv`
2. Activate it:
   `.venv\Scripts\Activate.ps1`
3. Install dependencies:
   `python -m pip install -r requirements.txt`
4. Install Tesseract OCR for Windows and ensure `tesseract.exe` is on PATH.
5. Run the app:
   `python app.py`

## Run tests

`pytest -q`

## Privacy and validation

- Medical-document validation is enforced on the backend before any report analysis proceeds.
- Unsupported, empty, oversized, unreadable, and irrelevant documents are explicitly rejected.
- Medical documents are processed in memory and are not persisted by the report-validation flow. The offline assistant keeps extracted report context in bounded process memory for up to 30 minutes; it is not durable and is cleared when the application restarts.
- Video analysis is a separate upload pipeline for MP4, MOV, and AVI files. It checks container signatures, decoding, duration, and frame rate; it only returns an experimental heart-rate estimate when a face-region signal passes basic quality checks. Missing or poor-quality signals do not produce a fabricated BPM.

The experimental video analysis requires NumPy, SciPy, and OpenCV. On Windows, install the project requirements and restart Flask after changing them:

`python -m pip install -r requirements.txt`

Live monitoring uses the browser's camera permission and performs sampling locally. Position the forehead inside the visible guide; this prototype does not automatically detect or track a face. The camera-derived estimate is experimental, requires at least 20 seconds of usable signal, and is not medically validated.

## Project status

The interface is a responsive, single-page website for medical-document validation, report value extraction, an offline report assistant, experimental uploaded-video rPPG analysis, and browser-local manual-ROI webcam sampling. Automatic face tracking, clinically validated measurements, external AI integration, and research-dataset evaluation are not implemented.
