import io

from reportlab.pdfgen import canvas

from app.services.report_reader import ReportReaderService


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
    pdf.setTitle('Medical report')
    for idx, line in enumerate(text.splitlines()[:20]):
        pdf.drawString(60, 760 - idx * 18, line[:100])
    pdf.save()
    return buffer.getvalue()


def test_report_extraction_reads_values_and_ranges():
    service = ReportReaderService(upload_dir='tmp_uploads_reader_test')
    text = """CBC REPORT
Hemoglobin: 10.5 g/dL
Reference range: 12-16 g/dL
WBC: 8.2 x10^3/uL
Reference range: 4-11 x10^3/uL"""
    result = service.extract_report(MockFile('cbc.pdf', _make_pdf(text), 'application/pdf'))
    assert result['accepted'] is True
    assert len(result['tests']) >= 2
    assert any(item['label'] == 'Hemoglobin' for item in result['tests'])
    assert result['abnormal_values']
    hemoglobin = next(item for item in result['tests'] if item['label'] == 'Hemoglobin')
    assert hemoglobin['status'] == 'outside stated range'


def test_report_without_reference_range_requires_manual_verification():
    service = ReportReaderService(upload_dir='tmp_uploads_reader_no_range_test')
    text = """CBC REPORT
Hemoglobin: 10.5 g/dL
WBC: 8.2 x10^3/uL"""
    result = service.extract_report(MockFile('cbc.pdf', _make_pdf(text), 'application/pdf'))
    assert result['accepted'] is True
    assert all(item['status'] == 'manual verification' for item in result['tests'])
    assert 'manual verification' in result['summary']


def test_report_assistant_refuses_to_invent_missing_values():
    from app.services.ai_assistant import MedicalAssistantService

    assistant = MedicalAssistantService()
    answer = assistant.answer_question('Which values are abnormal?', 'Hemoglobin: 12.8 g/dL\nReference range: 12-16 g/dL', [])
    assert 'not find any values clearly outside' in answer.lower()


def test_assistant_endpoint_requires_a_validated_server_report_context():
    from app import create_app

    client = create_app().test_client()
    response = client.post(
        '/api/ask-assistant',
        json={
            'question': 'Summarize this report',
            'report_text': 'FAKE REPORT: all tests normal',
            'abnormalities': [],
        },
    )
    assert response.status_code == 400


def test_assistant_endpoint_uses_report_context_created_by_reader():
    from app import create_app

    client = create_app().test_client()
    pdf = _make_pdf("""CBC REPORT
Hemoglobin: 10.5 g/dL
Reference range: 12-16 g/dL""")
    upload = client.post(
        '/api/report-reader',
        data={'file': (io.BytesIO(pdf), 'cbc.pdf')},
        content_type='multipart/form-data',
    )
    assert upload.status_code == 200
    payload = upload.get_json()
    assert payload['report_id']

    answer = client.post(
        '/api/ask-assistant',
        json={'question': 'Which values are abnormal?', 'report_id': payload['report_id']},
    )
    assert answer.status_code == 200
    assert 'Hemoglobin' in answer.get_json()['answer']
