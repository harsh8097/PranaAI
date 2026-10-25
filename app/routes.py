import os
from flask import Blueprint, jsonify, render_template, request, send_from_directory

from app.services.ai_assistant import MedicalAssistantService
from app.services.document_validation import DocumentValidationService
from app.services.report_reader import ReportReaderService
from app.services.video_analysis import VideoAnalysisService

bp = Blueprint("main", __name__)
service = DocumentValidationService(upload_dir="tmp_uploads")
reader_service = ReportReaderService(upload_dir="tmp_uploads")
assistant_service = MedicalAssistantService()
video_service = VideoAnalysisService()


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/download-app")
@bp.route("/prana_mobile_app.zip")
def download_mobile_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(base_dir, "prana_mobile_app.zip", as_attachment=True)


@bp.route("/api/validate-document", methods=["POST"])
def validate_document():
    file_storage = request.files.get("file")
    result = service.process_upload(file_storage)

    if result.accepted:
        # Directly extract diagnostic parameters so validation response contains full lab data
        extracted = {}
        report_id = ""
        try:
            if file_storage:
                file_storage.seek(0)
                extracted = reader_service.extract_report(file_storage)
                if extracted.get("accepted"):
                    report_id = assistant_service.store_report_context(
                        extracted.get("document_text", ""),
                        extracted.get("abnormal_values", []),
                    )
        except Exception:
            extracted = {}
            report_id = ""

        return jsonify(
            {
                "accepted": True,
                "status": result.status,
                "alert": "",
                "file_type": result.file_type,
                "page_count": result.page_count,
                "confidence": result.confidence,
                "reason": result.reason,
                "message": "Medical document accepted and diagnostic parameters extracted.",
                "tests": extracted.get("tests", []),
                "abnormal_values": extracted.get("abnormal_values", []),
                "patient_condition": extracted.get("patient_condition"),
                "summary": extracted.get("summary", ""),
                "report_id": report_id,
            }
        )

    return jsonify(
        {
            "accepted": False,
            "status": result.status,
            "alert": result.alert,
            "file_type": result.file_type,
            "page_count": result.page_count,
            "reason": result.reason,
            "message": result.alert,
        }
    ), 400


@bp.route("/api/medical-analysis", methods=["POST"])
def medical_analysis():
    file_storage = request.files.get("file")
    result = service.process_upload(file_storage)
    if not result.accepted:
        return jsonify({"accepted": False, "alert": result.alert, "status": result.status}), 400
    return jsonify({"accepted": True, "status": result.status, "message": "Medical document passed validation and can proceed to report analysis."})


@bp.route("/api/report-reader", methods=["POST"])
def report_reader():
    file_storage = request.files.get("file")
    result = reader_service.extract_report(file_storage)
    if not result.get("accepted"):
        return jsonify({"accepted": False, "alert": result.get("alert", "Document rejected."), "status": result.get("status", "REJECTED")}), 400
    result["report_id"] = assistant_service.store_report_context(
        result["document_text"],
        result["abnormal_values"],
    )
    return jsonify(result)


@bp.route("/api/ask-assistant", methods=["POST"])
def ask_assistant():
    data = request.get_json(silent=True) or {}
    question = data.get("question") or ""
    report_id = data.get("report_id") or ""
    if not isinstance(question, str) or not question.strip() or not isinstance(report_id, str) or not report_id:
        return jsonify({"error": "A question and a valid report context are required."}), 400
    answer = assistant_service.answer_for_report(report_id, question)
    if answer is None:
        return jsonify({"error": "The report context is missing or expired. Upload and validate the report again."}), 404
    return jsonify({"answer": answer})


@bp.route("/api/video-analysis", methods=["POST"])
def analyze_video():
    result = video_service.analyze(request.files.get("file"))
    return jsonify(result), 200 if result["accepted"] else 400


@bp.route("/api/cleanup-temp-files", methods=["POST"])
def cleanup_temp_files():
    removed = service.cleanup_expired_uploads()
    return jsonify({"removed": removed, "count": len(removed)})


@bp.route("/live-monitor")
def live_monitor():
    return render_template("index.html", active_section="monitor")


@bp.route("/video-analysis")
def video_analysis():
    return render_template("index.html", active_section="video")
