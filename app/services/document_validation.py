import io
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import fitz
import pytesseract
from PIL import Image, ImageOps


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None or os.environ.get("TESSERACT_CMD") is not None

MEDICAL_KEYWORDS = {
    "cbc", "complete blood count", "hemoglobin", "hgb", "wbc", "rbc", "platelets", "mcv", "mch",
    "malaria", "parasite", "thick film", "thin film", "blood smear", "prescription", "medication",
    "discharge summary", "radiology", "x-ray", "ct scan", "mri", "report", "findings", "interpretation",
    "ref range", "reference range", "normal range", "lab", "serum", "bilirubin", "creatinine", "alt",
    "ast", "glucose", "cholesterol", "tsh", "urine", "culture", "specimen", "patient", "hospital",
}

SPECIFIC_MEDICAL_KEYWORDS = {
    "cbc", "complete blood count", "hemoglobin", "hgb", "wbc", "rbc", "platelets", "mcv", "mch",
    "malaria", "parasite", "thick film", "thin film", "blood smear", "prescription", "medication",
    "discharge summary", "radiology", "x-ray", "ct scan", "mri", "serum", "bilirubin", "creatinine",
    "alt", "ast", "glucose", "cholesterol", "tsh", "urine", "culture",
}

STRUCTURE_KEYWORDS = {
    "patient", "age", "sex", "date", "mrn", "uhid", "sample", "specimen", "result", "unit", "reference",
    "normal", "abnormal", "report no", "test name", "clinical findings", "diagnosis", "medication",
    "doctor", "hospital", "lab", "investigation", "report date",
}

IRRELEVANT_KEYWORDS = {
    "invoice", "receipt", "payment", "total", "due", "qty", "price", "po box", "order id", "customer",
    "school", "assignment", "homework", "teacher", "class", "semester", "exam", "essay", "chapter",
    "recipe", "ingredients", "servings", "bake", "prep time", "cook time", "oven", "flour", "sugar",
    "letter", "cv", "resume", "job", "cover letter", "application", "salary", "offer",
    "complaint", "ticket", "booking", "hotel", "flight", "travel",
}

ALERTS = {
    "IRRELEVANT_DOCUMENT": "⚠️ Irrelevant Document Detected. PranaScan AI accepts only medical documents, such as blood-test reports, malaria reports, prescriptions, discharge summaries, and radiology reports. Please upload a relevant medical document.",
    "UNREADABLE_OR_LOW_QUALITY": "⚠️ Unable to Read This Document. The file may be blurry, incomplete, corrupted, or contain insufficient readable text. Please upload a clearer medical document.",
    "UNSUPPORTED_OR_INVALID_FILE": "⚠️ Unsupported File Format. Please upload a valid PDF, PNG, JPG, or JPEG medical document.",
    "UNCERTAIN_DOCUMENT": "⚠️ Medical Document Not Confirmed. We could not confidently identify this file as a medical report. Please verify the document and upload it again.",
    "UPLOAD_TOO_LARGE": "⚠️ File Size Limit Exceeded. Please upload a smaller document.",
}


@dataclass
class DocumentValidationResult:
    status: str
    alert: str
    accepted: bool
    file_type: str
    page_count: int
    extracted_text: str
    confidence: float
    reason: str
    temp_path: Optional[str] = None
    file_name: str = ""
    mime_type: str = ""
    is_pdf: bool = False
    is_image: bool = False
    metadata: dict = field(default_factory=dict)


def normalize_extracted_text(text: str) -> str:
    if not text:
        return ""
    chars = []
    for char in text:
        code = ord(char)
        if 0xF020 <= code <= 0xF0FE:
            chars.append(chr(code - 0xF000))
        elif 0xF000 <= code <= 0xF0FF:
            chars.append(" " if (code - 0xF000) < 32 else chr(code - 0xF000))
        else:
            chars.append(char)
    return "".join(chars)


class DocumentValidationService:
    def __init__(self, upload_dir: str = "tmp_uploads", max_size_mb: int = 10):
        self.upload_dir = Path(upload_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _ocr_image(self, image) -> str:
        if not TESSERACT_AVAILABLE:
            return ""
        try:
            return pytesseract.image_to_string(image, config="--psm 6")
        except Exception:
            return ""

    def process_upload(self, file_storage, max_size_bytes: Optional[int] = None) -> DocumentValidationResult:
        if file_storage is None or file_storage.filename in (None, ""):
            return DocumentValidationResult(
                status="UNSUPPORTED_OR_INVALID_FILE",
                alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                accepted=False,
                file_type="unknown",
                page_count=0,
                extracted_text="",
                confidence=0.0,
                reason="No file was uploaded.",
            )

        size_limit = max_size_bytes or self.max_size_bytes
        data = file_storage.read(size_limit + 1)
        if not data or len(data) == 0:
            return DocumentValidationResult(
                status="UNSUPPORTED_OR_INVALID_FILE",
                alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                accepted=False,
                file_type="empty",
                page_count=0,
                extracted_text="",
                confidence=0.0,
                reason="Uploaded file is empty.",
            )

        if len(data) > size_limit:
            return DocumentValidationResult(
                status="UPLOAD_TOO_LARGE",
                alert=ALERTS["UPLOAD_TOO_LARGE"],
                accepted=False,
                file_type="unknown",
                page_count=0,
                extracted_text="",
                confidence=0.0,
                reason=f"File is {len(data)} bytes, above the {size_limit} byte limit.",
            )

        file_type = self.detect_actual_file_type(data, file_storage.filename)
        if file_type in ("unsupported", "invalid"):
            return DocumentValidationResult(
                status="UNSUPPORTED_OR_INVALID_FILE",
                alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                accepted=False,
                file_type="unsupported",
                page_count=0,
                extracted_text="",
                confidence=0.0,
                reason="File format is not supported or content is corrupted.",
            )

        has_embedded_images = False
        if file_type == "pdf":
            try:
                with fitz.open(stream=data, filetype="pdf") as document:
                    page_count = len(document)
                    if page_count == 0:
                        return DocumentValidationResult(
                            status="UNREADABLE_OR_LOW_QUALITY",
                            alert=ALERTS["UNREADABLE_OR_LOW_QUALITY"],
                            accepted=False,
                            file_type="pdf",
                            page_count=0,
                            extracted_text="",
                            confidence=0.0,
                            reason="PDF is malformed or contains no pages.",
                        )
                    if page_count > 50:
                        return DocumentValidationResult(
                            status="UNSUPPORTED_OR_INVALID_FILE",
                            alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                            accepted=False,
                            file_type="pdf",
                            page_count=page_count,
                            extracted_text="",
                            confidence=0.0,
                            reason="PDF exceeds the 50-page processing limit.",
                        )
                    extracted_pages = []
                    for page_index in range(page_count):
                        page = document[page_index]
                        if len(page.get_images()) > 0:
                            has_embedded_images = True
                        raw_text = normalize_extracted_text(page.get_text("text") or "")
                        words = page.get_text("words")
                        aligned_str = ""
                        if words:
                            lines_by_y = {}
                            for w in words:
                                y_approx = round(w[1] / 4.0) * 4.0
                                lines_by_y.setdefault(y_approx, []).append(w)
                            aligned_lines = []
                            for y in sorted(lines_by_y.keys()):
                                lw = sorted(lines_by_y[y], key=lambda x: x[0])
                                l_txt = " ".join(normalize_extracted_text(w[4]) for w in lw).strip()
                                if l_txt:
                                    aligned_lines.append(l_txt)
                            aligned_str = "\n".join(aligned_lines)

                        text = raw_text
                        if aligned_str and aligned_str != raw_text:
                            text = f"{raw_text}\n{aligned_str}"

                        if not text or len(text.strip()) < 20:
                            try:
                                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                image = Image.open(io.BytesIO(pix.tobytes("png")))
                                ocr_text = self._ocr_image(image)
                                if ocr_text:
                                    text = ocr_text
                            except Exception:
                                pass
                        extracted_pages.append(text)
                    extracted_text = "\n".join(extracted_pages)
            except Exception:
                return DocumentValidationResult(
                    status="UNSUPPORTED_OR_INVALID_FILE",
                    alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                    accepted=False,
                    file_type="pdf",
                    page_count=0,
                    extracted_text="",
                    confidence=0.0,
                    reason="The PDF could not be parsed and may be corrupted.",
                )
        elif file_type in {"png", "jpg", "jpeg"}:
            try:
                with Image.open(io.BytesIO(data)) as image:
                    image = ImageOps.exif_transpose(image)
                    image = image.convert("RGB")
                    if image.size[0] == 0 or image.size[1] == 0:
                        raise ValueError("Image size is invalid.")
                    has_embedded_images = True
                    extracted_text = self._ocr_image(image)
                    page_count = 1
            except Exception:
                return DocumentValidationResult(
                    status="UNREADABLE_OR_LOW_QUALITY",
                    alert=ALERTS["UNREADABLE_OR_LOW_QUALITY"],
                    accepted=False,
                    file_type=file_type,
                    page_count=0,
                    extracted_text="",
                    confidence=0.0,
                    reason="The uploaded image could not be decoded or read reliably.",
                )
        else:
            return DocumentValidationResult(
                status="UNSUPPORTED_OR_INVALID_FILE",
                alert=ALERTS["UNSUPPORTED_OR_INVALID_FILE"],
                accepted=False,
                file_type="unsupported",
                page_count=0,
                extracted_text="",
                confidence=0.0,
                reason="Unsupported file type.",
            )

        is_radiology = bool(
            re.search(
                r"(?i)(xray|x-ray|radiology|mri|ct\s*scan|ultrasound|sonography|mammogram|pet\s*scan|fluoroscopy|scan)",
                file_storage.filename or "",
            )
        )
        if not extracted_text.strip() and is_radiology and (has_embedded_images or file_type in {"png", "jpg", "jpeg"}):
            classification = {
                "status": "RELEVANT_MEDICAL_DOCUMENT",
                "alert": "",
                "accepted": True,
                "confidence": 0.90,
                "reason": "Medical radiology / diagnostic imaging document accepted for review.",
            }
        else:
            classification = self.classify_document(extracted_text)
        return DocumentValidationResult(
            status=classification["status"],
            alert=classification["alert"],
            accepted=classification["accepted"],
            file_type=file_type,
            page_count=page_count,
            extracted_text=extracted_text,
            confidence=classification["confidence"],
            reason=classification["reason"],
            temp_path=None,
            file_name=file_storage.filename,
            mime_type=file_storage.mimetype or "application/octet-stream",
            is_pdf=file_type == "pdf",
            is_image=file_type in {"png", "jpg", "jpeg"},
            metadata={"created_at": datetime.now(timezone.utc).isoformat()},
        )

    def detect_actual_file_type(self, data: bytes, filename: str) -> str:
        if not data:
            return "invalid"
        if data.startswith(b"%PDF"):
            return "pdf"

        extension = Path(filename).suffix.lower().lstrip(".")
        if extension in {"png", "jpg", "jpeg"}:
            try:
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()
                return extension
            except Exception:
                return "invalid"

        if extension == "pdf":
            try:
                fitz.open(stream=data, filetype="pdf")
                return "pdf"
            except Exception:
                return "invalid"

        return "unsupported"

    def classify_document(self, text: str) -> dict:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        lowered = cleaned.lower()
        if not cleaned:
            return {
                "status": "UNREADABLE_OR_LOW_QUALITY",
                "alert": ALERTS["UNREADABLE_OR_LOW_QUALITY"],
                "accepted": False,
                "confidence": 0.0,
                "reason": "No readable text was extracted from the document.",
            }

        negative_hits = sum(1 for term in IRRELEVANT_KEYWORDS if term in lowered)
        medical_hits = sum(1 for term in MEDICAL_KEYWORDS if term in lowered)
        specific_medical_hits = sum(1 for term in SPECIFIC_MEDICAL_KEYWORDS if term in lowered)
        structure_hits = sum(1 for term in STRUCTURE_KEYWORDS if term in lowered)
        unit_score = 1 if re.search(r"\d+(?:\.\d+)?\s*(?:mg|g/dl|mmol|u/l|cells/ul|%|mmhg|fL|pg)", lowered) else 0
        range_score = 1 if re.search(r"reference\s*(range|value)|normal\s*(range|value)|ref\s*range|\b\d+\.?\d*\s*[-–]\s*\d+\.?\d*\b", lowered) else 0
        score = (medical_hits * 2) + (structure_hits * 2) + unit_score + range_score

        if negative_hits >= 2 and medical_hits == 0 and not (range_score or unit_score):
            return {
                "status": "IRRELEVANT_DOCUMENT",
                "alert": ALERTS["IRRELEVANT_DOCUMENT"],
                "accepted": False,
                "confidence": 0.12,
                "reason": "The content looks like a non-medical document and lacks medical-report evidence.",
            }

        if specific_medical_hits >= 1 and score >= 8 and (structure_hits >= 1 or unit_score or range_score):
            return {
                "status": "RELEVANT_MEDICAL_DOCUMENT",
                "alert": "",
                "accepted": True,
                "confidence": min(0.96, round((score / 14.0), 2)),
                "reason": "The document includes specific medical terminology, report structure, and supporting clinical indicators.",
            }

        if len(cleaned) < 40:
            return {
                "status": "UNREADABLE_OR_LOW_QUALITY",
                "alert": ALERTS["UNREADABLE_OR_LOW_QUALITY"],
                "accepted": False,
                "confidence": 0.2,
                "reason": "The document does not contain enough readable text to confirm it is a medical report.",
            }

        if medical_hits >= 1 or structure_hits >= 1:
            return {
                "status": "UNCERTAIN_DOCUMENT",
                "alert": ALERTS["UNCERTAIN_DOCUMENT"],
                "accepted": False,
                "confidence": 0.31,
                "reason": "Some medical wording was found, but the document lacks enough structure or evidence to confirm a legitimate report.",
            }

        return {
            "status": "IRRELEVANT_DOCUMENT",
            "alert": ALERTS["IRRELEVANT_DOCUMENT"],
            "accepted": False,
            "confidence": 0.18,
            "reason": "The content appears unrelated to medical reporting.",
        }

    def cleanup_expired_uploads(self, max_age_hours: int = 24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        removed = []
        for file_path in self.upload_dir.iterdir():
            try:
                last_modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if last_modified < cutoff:
                    file_path.unlink(missing_ok=True)
                    removed.append(str(file_path))
            except Exception:
                continue
        return removed
