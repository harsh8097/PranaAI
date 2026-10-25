import io

from reportlab.pdfgen import canvas

from app import create_app
from app.services.document_validation import DocumentValidationService


class MockFile:
    def __init__(self, filename, data, mimetype):
        self.filename = filename
        self.mimetype = mimetype
        self._data = data

    def read(self, size=-1):
        return self._data if size < 0 else self._data[:size]


def _make_pdf(text):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle("Medical report")
    pdf.setFont("Helvetica", 12)
    for idx, line in enumerate(text.splitlines()[:25]):
        pdf.drawString(60, 760 - idx * 18, line[:100])
    pdf.save()
    return buffer.getvalue()


def _make_image_bytes():
    from PIL import Image

    image = Image.new("RGB", (120, 80), color="white")
    return image.tobytes()


def test_valid_cbc_report_is_accepted():
    service = DocumentValidationService(upload_dir="tmp_uploads_test")
    text = """CBC REPORT
Patient: Asha Sharma
Hemoglobin: 12.8 g/dL
WBC: 7.6 x10^3/uL
Platelets: 245 x10^3/uL
Reference Range: Hb 12-16 g/dL; WBC 4-11; Platelets 150-450"""
    result = service.process_upload(MockFile("cbc_report.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is True
    assert result.status == "RELEVANT_MEDICAL_DOCUMENT"


def test_valid_malaria_report_is_accepted():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_2")
    text = """MALARIA TEST REPORT
Specimen: Blood smear
Peripheral smear: Malaria parasite seen
Parasite species: Plasmodium vivax
Result: Positive
Reference range: Negative
"""
    result = service.process_upload(MockFile("malaria_report.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is True
    assert result.status == "RELEVANT_MEDICAL_DOCUMENT"


def test_valid_prescription_is_accepted():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_3")
    text = """PRESCRIPTION
Dr. S. Mehta
Patient: Rahul Kumar
Medication: Amoxicillin 500 mg
Frequency: Twice daily for 5 days
Clinical note: Fever and cough"""
    result = service.process_upload(MockFile("prescription.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is True
    assert result.status == "RELEVANT_MEDICAL_DOCUMENT"


def test_valid_discharge_summary_is_accepted():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_4")
    text = """HOSPITAL DISCHARGE SUMMARY
Patient: Niharika Rao
Admission: 04/01/2026
Discharge: 06/01/2026
Diagnosis: Mild pneumonia
Treatment: IV antibiotics, oral hydration
Findings: Chest X-ray showed mild infiltrates
"""
    result = service.process_upload(MockFile("discharge_summary.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is True
    assert result.status == "RELEVANT_MEDICAL_DOCUMENT"


def test_invoice_is_rejected_as_irrelevant_document():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_5")
    text = """Invoice
Customer Name: Riya Patel
Total: 750.00
Due date: 15/06/2026
Description: Office chairs"""
    result = service.process_upload(MockFile("invoice.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is False
    assert result.status == "IRRELEVANT_DOCUMENT"


def test_school_assignment_is_rejected():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_6")
    text = """School Assignment
Biology class
Explain photosynthesis
Essay due Monday"""
    result = service.process_upload(MockFile("assignment.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is False
    assert result.status == "IRRELEVANT_DOCUMENT"


def test_recipe_is_rejected():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_7")
    text = """Recipe for Paneer Curry
Ingredients: paneer, tomato, onion, spices
Prep time: 20 min
Cook time: 30 min"""
    result = service.process_upload(MockFile("recipe.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is False
    assert result.status == "IRRELEVANT_DOCUMENT"


def test_empty_file_is_rejected():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_8")
    result = service.process_upload(MockFile("empty.pdf", b"", "application/pdf"))
    assert result.accepted is False
    assert result.status == "UNSUPPORTED_OR_INVALID_FILE"


def test_corrupted_pdf_is_rejected_safely():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_9")
    result = service.process_upload(MockFile("corrupt.pdf", b"%PDF-1.4\nnot a valid pdf body", "application/pdf"))
    assert result.accepted is False
    assert result.status in {"UNSUPPORTED_OR_INVALID_FILE", "UNREADABLE_OR_LOW_QUALITY"}


def test_unsupported_file_type_is_rejected():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_10")
    result = service.process_upload(MockFile("lab_notes.txt", b"Blood pressure values", "text/plain"))
    assert result.accepted is False
    assert result.status == "UNSUPPORTED_OR_INVALID_FILE"


def test_unreadable_document_generates_warning():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_11")
    result = service.process_upload(MockFile("blurry.pdf", _make_pdf("..."), "application/pdf"))
    assert result.accepted is False
    assert result.status in {"UNREADABLE_OR_LOW_QUALITY", "UNCERTAIN_DOCUMENT"}


def test_uncertain_document_does_not_proceed_to_analysis():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_12")
    text = """Report
Blood health check
Maybe medical note
"""
    result = service.process_upload(MockFile("uncertain.pdf", _make_pdf(text), "application/pdf"))
    assert result.accepted is False
    assert result.status in {"UNCERTAIN_DOCUMENT", "UNREADABLE_OR_LOW_QUALITY"}


def test_generic_report_words_do_not_accept_school_document():
    service = DocumentValidationService(upload_dir="tmp_uploads_test_generic_school")
    result = service.classify_document(
        "Report for patient age date result unit and reference section."
    )
    assert result["accepted"] is False
    assert result["status"] != "RELEVANT_MEDICAL_DOCUMENT"


def test_rejected_document_never_reaches_medical_analysis_endpoint():
    app = create_app()
    client = app.test_client()
    response = client.post(
        "/api/medical-analysis",
        data={"file": (io.BytesIO(b"not a valid medical document"), "invoice.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["accepted"] is False


def test_frontend_validation_cannot_bypass_backend_validation():
    app = create_app()
    client = app.test_client()
    response = client.post(
        "/api/validate-document",
        data={"file": (io.BytesIO(b"School assignment with teacher details and exam deadlines"), "assignment.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "UNSUPPORTED_OR_INVALID_FILE"


def test_upload_is_not_persisted_after_processing(tmp_path):
    upload_dir = tmp_path / "uploads"
    service = DocumentValidationService(upload_dir=str(upload_dir))
    result = service.process_upload(
        MockFile(
            "cbc.pdf",
            _make_pdf(
                """CBC REPORT
Patient: Synthetic Example
Hemoglobin: 10.2 g/dL
WBC: 7.2 x10^3/uL
Reference range: 12-16 g/dL"""
            ),
            "application/pdf",
        )
    )
    assert result.accepted
    assert result.temp_path is None
    assert list(upload_dir.iterdir()) == []
