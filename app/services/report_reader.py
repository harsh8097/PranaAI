import re
from typing import List

from app.services.document_validation import DocumentValidationService


class ReportReaderService:
    def __init__(self, upload_dir: str = "tmp_uploads"):
        self.validation_service = DocumentValidationService(upload_dir=upload_dir)

    def extract_report(self, file_storage) -> dict:
        validation = self.validation_service.process_upload(file_storage)
        if not validation.accepted:
            return {
                "accepted": False,
                "status": validation.status,
                "alert": validation.alert,
                "message": validation.alert,
            }

        text = validation.extracted_text or ""
        normalized = self._normalize_text(text)
        tests = self._extract_tests(normalized)
        abnormalities = self._find_abnormalities(tests)
        abnormal_labels = {item["label"].casefold() for item in abnormalities}
        for item in tests:
            if item["label"].casefold() in abnormal_labels:
                item["status"] = "outside stated range"
            elif not item["reference_range"]:
                item["status"] = "manual verification"

        if abnormalities:
            patient_condition = {
                "status": "ATTENTION_REQUIRED",
                "is_well": False,
                "badge": "Patient Condition: Attention Required · Abnormal Values Detected",
                "tone": "danger",
                "summary": f"{len(abnormalities)} lab parameter(s) detected outside reference ranges.",
            }
        elif tests:
            patient_condition = {
                "status": "WELL_CONDITION",
                "is_well": True,
                "badge": "Patient Condition: Well Condition · All Extracted Tests Normal",
                "tone": "success",
                "summary": "All readable test measurements fall within printed normal reference ranges.",
            }
        else:
            patient_condition = {
                "status": "MANUAL_REVIEW",
                "is_well": None,
                "badge": "Patient Condition: Manual Verification Needed",
                "tone": "neutral",
                "summary": "No numerical lab measurements could be extracted automatically.",
            }

        structured = {
            "accepted": True,
            "status": validation.status,
            "file_type": validation.file_type,
            "page_count": validation.page_count,
            "document_text": text,
            "tests": tests,
            "abnormal_values": abnormalities,
            "patient_condition": patient_condition,
            "summary": self._summarize(text, tests, abnormalities),
            "requires_manual_review": not bool(tests),
        }
        return structured

    def _normalize_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    NON_TEST_WORDS = {
        "patient", "age", "sex", "gender", "date", "mrn", "uhid", "name", "lab no", "ref by",
        "collected", "reported", "a/c status", "new delhi", "delhi", "sector", "block", "iso",
        "tel", "phone", "dr", "page", "result", "units", "bio ref interval", "bio ref", "test name",
        "test report", "interim", "sample", "specimen"
    }

    def _extract_tests(self, text: str) -> List[dict]:
        tests = []
        seen = set()
        lines = text.splitlines()
        idx = 0

        # Pattern 1: Label with colon/dash separator: "Hemoglobin: 12.8 g/dL"
        pattern_delim = re.compile(
            r"(?i)^[|\s]*([A-Za-z][A-Za-z0-9/\-,\s()]+?)\s*[:\-]\s*([-+]?\d+(?:\.\d+)?)\s*(mg/dL|g/dL|mmol/L|mmol|u/L|U/L|fL|pg|%|x10\^3/uL|cells/uL|IU/L|ng/L|mcg/dL|mg/L|mmHg)?\b"
        )
        # Pattern 2: Tabular / aligned row: "APOLIPOPROTEIN B (Apo B) 46.00 mg/dL 46 - 174"
        pattern_tabular = re.compile(
            r"(?i)^[|\s]*([A-Za-z][A-Za-z0-9/\-,\s()]{2,60}?)\s+([-+]?\d+(?:\.\d+)?)\s*(mg/dL|g/dL|mmol/L|mmol|u/L|U/L|fL|pg|%|x10\^3/uL|cells/uL|IU/L|ng/L|mcg/dL|mg/L|mmHg)\b"
        )

        while idx < len(lines):
            line = lines[idx].strip()
            if not line:
                idx += 1
                continue

            match = pattern_delim.search(line) or pattern_tabular.search(line)
            if not match:
                idx += 1
                continue

            label = self._clean_label(match.group(1))
            try:
                value = float(match.group(2))
            except ValueError:
                idx += 1
                continue
            unit = (match.group(3) or "").strip()

            if not label or label.lower() in self.NON_TEST_WORDS or any(bad in label.lower() for bad in ["new delhi", "sector", "block e", "iso 9001", "lab no", "production test"]) or any(u in label.lower() for u in ["mg/dl", "g/dl", "mmol/l", "u/l", "ng/l", "cells/ul"]):
                idx += 1
                continue

            # Look for range in the same line after the matched portion
            remaining_line = line[match.end():].strip()
            range_text = self._extract_reference_range_for_line(remaining_line) or self._extract_reference_range_for_line(line)
            if not range_text and idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                if any(kw in next_line.lower() for kw in ["reference", "range", "bio. ref"]):
                    range_text = self._extract_reference_range_for_line(next_line)
                    idx += 1

            key = (label.lower(), value, unit)
            if key in seen:
                idx += 1
                continue
            seen.add(key)
            tests.append({
                "label": label,
                "value": value,
                "unit": unit,
                "reference_range": range_text,
                "status": "within range" if range_text else "manual verification",
            })
            idx += 1

        if not tests:
            for line in lines:
                match = re.search(r"(?i)([A-Za-z][A-Za-z0-9/\-\s()]{2,50}?)\s+(?:=|:|\-)?\s*([-+]?\d+(?:\.\d+)?)\s*(mg/dL|g/dL|mmol/L|u/L|U/L|fL|pg|%|x10\^3/uL|cells/uL|IU/L|ng/L|mcg/dL|mg/L|mmHg)?", line)
                if not match:
                    continue
                label = self._clean_label(match.group(1))
                if not label or label.lower() in self.NON_TEST_WORDS:
                    continue
                try:
                    value = float(match.group(2))
                except ValueError:
                    continue
                unit = (match.group(3) or "").strip()
                tests.append({
                    "label": label,
                    "value": value,
                    "unit": unit,
                    "reference_range": self._extract_reference_range_for_line(line),
                    "status": "manual verification",
                })
        return tests

    def _extract_reference_range_for_line(self, line: str):
        if not line:
            return ""
        reference_match = re.search(r"(?i)(?:reference\s*range|normal\s*range|ref\s*range|bio\.\s*ref\.\s*interval|range)\s*[:\-]?\s*([A-Za-z0-9\-–/\s.<>]+)", line)
        if reference_match:
            candidate = reference_match.group(1).strip()
            # Clean candidate up to semicolon or pipe if present
            candidate = candidate.split(";")[0].split("|")[0].strip()
            if candidate:
                return candidate
        ineq_match = re.search(r"([<>]\s*=?\s*\d+(?:\.\d+)?)", line)
        if ineq_match:
            return ineq_match.group(1).strip()
        range_match = re.search(r"(\d+(?:\.\d+)?\s*(?:-|to|–)\s*\d+(?:\.\d+)?)\s*(?:mg/dL|g/dL|mmol/L|u/L|U/L|%|x10\^3/uL)?", line)
        if range_match:
            return range_match.group(1).strip()
        return ""

    def _clean_label(self, label: str) -> str:
        cleaned = re.sub(r"\s+", " ", label).strip(" :;|-")
        if len(cleaned) < 2:
            return ""
        return cleaned

    def _find_abnormalities(self, tests: List[dict]):
        abnormal = []
        for item in tests:
            range_text = item.get("reference_range", "")
            if not range_text:
                continue
            lower_bound, upper_bound = self._parse_range(range_text)
            value = item.get("value")
            if value is None:
                continue
            is_abnormal = False
            if lower_bound is not None and value < lower_bound:
                is_abnormal = True
            if upper_bound is not None and value > upper_bound:
                is_abnormal = True

            if is_abnormal:
                abnormal.append({
                    "label": item["label"],
                    "value": value,
                    "unit": item.get("unit", ""),
                    "reference_range": range_text,
                })
        return abnormal

    def _parse_range(self, range_text: str):
        if not range_text:
            return None, None
        lt_match = re.search(r"<\s*=?\s*([-+]?\d+(?:\.\d+)?)", range_text)
        if lt_match:
            return None, float(lt_match.group(1))
        gt_match = re.search(r">\s*=?\s*([-+]?\d+(?:\.\d+)?)", range_text)
        if gt_match:
            return float(gt_match.group(1)), None
        match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:-|to|–)\s*([-+]?\d+(?:\.\d+)?)", range_text)
        if match:
            return float(match.group(1)), float(match.group(2))
        match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(?:\(|\[)\s*([-+]?\d+(?:\.\d+)?)\s*(?:\)|\])", range_text)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None

    def _summarize(self, text: str, tests: List[dict], abnormalities: List[dict]) -> str:
        if not tests:
            return "No structured numeric results were confidently extracted. Manual verification is required."
        first_test = tests[0].get("label", "document")
        if abnormalities:
            labels = ", ".join(item["label"] for item in abnormalities[:3])
            return f"The report contains {len(tests)} identifiable results and the following values appear outside the stated reference range: {labels}."
        if any(not item.get("reference_range") for item in tests):
            return f"The report includes {len(tests)} extracted measurements. None of the results with readable stated ranges were identified as outside those ranges; some results lack a readable range and require manual verification."
        return f"The report includes {len(tests)} extracted measurements, beginning with {first_test}. No values were identified as falling outside the printed reference ranges."
