import secrets
import threading
import time
from collections import OrderedDict


class MedicalAssistantService:
    def __init__(self, context_ttl_seconds: int = 1800, max_contexts: int = 100):
        self._context_ttl_seconds = context_ttl_seconds
        self._max_contexts = max_contexts
        self._contexts = OrderedDict()
        self._contexts_lock = threading.Lock()

    def store_report_context(self, extracted_text: str, abnormalities: list) -> str:
        report_id = secrets.token_urlsafe(32)
        now = time.monotonic()
        with self._contexts_lock:
            self._remove_expired_contexts(now)
            self._contexts[report_id] = {
                "created_at": now,
                "extracted_text": extracted_text,
                "abnormalities": abnormalities,
            }
            while len(self._contexts) > self._max_contexts:
                self._contexts.popitem(last=False)
        return report_id

    def answer_for_report(self, report_id: str, question: str) -> str | None:
        now = time.monotonic()
        with self._contexts_lock:
            self._remove_expired_contexts(now)
            context = self._contexts.get(report_id)
            if context is None:
                return None
            context["created_at"] = now
            self._contexts.move_to_end(report_id)
        return self.answer_question(
            question,
            context["extracted_text"],
            context["abnormalities"],
        )

    def _remove_expired_contexts(self, now: float) -> None:
        expired = [
            report_id
            for report_id, context in self._contexts.items()
            if now - context["created_at"] > self._context_ttl_seconds
        ]
        for report_id in expired:
            del self._contexts[report_id]

    def answer_question(self, question: str, extracted_text: str, abnormalities: list) -> str:
        if not extracted_text or not extracted_text.strip():
            return "No validated report text is available. Please upload a medical document and confirm it passes validation before asking questions."

        q = (question or "").lower()
        report_lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]

        if "summarize" in q or "summary" in q:
            return self._summarize_report(report_lines, abnormalities)

        if "explain" in q or "what is" in q or "meaning" in q:
            return self._explain_terms(report_lines, q)

        if "outside" in q or "abnormal" in q or "high" in q or "low" in q:
            if not abnormalities:
                return "I did not find any values clearly outside the printed reference ranges in the uploaded document. If some values are missing or unclear, manual verification is still required."
            items = "; ".join(f"{x['label']} = {x['value']} {x['unit']} (reference: {x['reference_range']})" for x in abnormalities[:5])
            return f"The report indicates the following values outside the stated reference range: {items}."

        if "radiology" in q or "finding" in q or "findings" in q:
            return self._describe_findings(report_lines)

        if "question" in q or "doctor" in q:
            return "Useful questions to ask your doctor include: What do these values mean for my current condition? Which values need follow-up or repeat testing? Are there any symptoms or medications that should be considered alongside this report?"

        return self._fallback_response(report_lines, abnormalities)

    def _summarize_report(self, report_lines: list, abnormalities: list) -> str:
        if len(report_lines) == 0:
            return "The uploaded report could not be read. Please upload a clearer medical document."
        if abnormalities:
            labels = ", ".join(item["label"] for item in abnormalities[:3])
            return f"The report contains medical findings and some values appear outside the document's printed reference ranges, including {labels}. The full interpretation should be reviewed by a qualified clinician."
        if any("manual verification" in line.lower() for line in report_lines):
            return "The uploaded report contains medical results, but some values or reference ranges may be missing or unclear. Review the original document and confirm the results with a clinician. This is not a diagnosis."
        return "The uploaded report appears to contain structured medical results and no values were identified outside readable printed reference ranges. This is not a diagnosis; a clinician should confirm the interpretation."

    def _explain_terms(self, report_lines: list, query: str) -> str:
        if not report_lines:
            return "The report text is not readable enough to explain terms accurately."
        for line in report_lines:
            lower = line.lower()
            if any(term in lower for term in ["hemoglobin", "wbc", "platelet", "cbc", "creatinine", "bilirubin", "glucose"]):
                if "hemoglobin" in lower:
                    return "Hemoglobin is the blood protein that carries oxygen. It is often reported in g/dL and can help indicate anemia or other blood-related conditions."
                if "wbc" in lower:
                    return "WBC stands for white blood cell count. It helps assess infection, inflammation, or bone-marrow issues."
                if "platelet" in lower:
                    return "Platelets help blood clot. Abnormal platelet counts can be associated with bleeding or clotting disorders."
                if "creatinine" in lower:
                    return "Creatinine is a kidney function marker. Higher-than-normal values may suggest reduced kidney function."
        return "I can explain the common lab terms in the report, but the document does not clearly show a term I can confidently define. Please ask about a specific test name such as hemoglobin, WBC, platelets, bilirubin, or creatinine."

    def _describe_findings(self, report_lines: list) -> str:
        for line in report_lines:
            lower = line.lower()
            if any(term in lower for term in ["finding", "findings", "radiology", "x-ray", "chest", "report"]):
                return f"This report mentions clinical findings. The original document text should be reviewed directly for the final interpretation. In general, radiology phrases describe the location, severity, and pattern of findings rather than a diagnosis by themselves."
        return "This document does not clearly contain radiology-specific findings. If the report is a written radiology report, please review the original text to interpret it correctly."

    def _fallback_response(self, report_lines: list, abnormalities: list) -> str:
        if abnormalities:
            sample = abnormalities[0]
            return f"Based on the uploaded report, {sample['label']} is outside the printed reference range. The document should be reviewed with a clinical professional before any decision is made."
        return "I can answer questions about the uploaded medical document’s numbers, reference ranges, and common terms. Ask me to summarize the report, explain a test, or list abnormal findings."
