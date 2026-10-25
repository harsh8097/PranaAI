class LabTestItem {
  final String label;
  final String value;
  final String unit;
  final String referenceRange;
  final String status;

  LabTestItem({
    required this.label,
    required this.value,
    required this.unit,
    required this.referenceRange,
    required this.status,
  });

  bool get isAbnormal => status == 'outside stated range';

  factory LabTestItem.fromJson(Map<String, dynamic> json) {
    return LabTestItem(
      label: json['label']?.toString() ?? '',
      value: json['value']?.toString() ?? '',
      unit: json['unit']?.toString() ?? '—',
      referenceRange: json['reference_range']?.toString() ?? 'Not stated',
      status: json['status']?.toString() ?? 'within range',
    );
  }

  Map<String, dynamic> toJson() => {
    'label': label,
    'value': value,
    'unit': unit,
    'reference_range': referenceRange,
    'status': status,
  };
}

class PatientCondition {
  final String badge;
  final String summary;
  final String tone;

  PatientCondition({
    required this.badge,
    required this.summary,
    required this.tone,
  });

  factory PatientCondition.fromJson(Map<String, dynamic> json) {
    return PatientCondition(
      badge: json['badge']?.toString() ?? 'Patient Condition Assessment',
      summary: json['summary']?.toString() ?? '',
      tone: json['tone']?.toString() ?? 'neutral',
    );
  }
}

class DiagnosticReport {
  final bool accepted;
  final String status;
  final double confidence;
  final String fileType;
  final String reason;
  final List<LabTestItem> tests;
  final List<String> abnormalValues;
  final PatientCondition? patientCondition;
  final String summary;
  final String reportId;

  DiagnosticReport({
    required this.accepted,
    required this.status,
    required this.confidence,
    required this.fileType,
    required this.reason,
    required this.tests,
    required this.abnormalValues,
    this.patientCondition,
    required this.summary,
    required this.reportId,
  });

  factory DiagnosticReport.fromJson(Map<String, dynamic> json) {
    var rawTests = json['tests'] as List<dynamic>? ?? [];
    List<LabTestItem> parsedTests = rawTests
        .map((item) => LabTestItem.fromJson(item as Map<String, dynamic>))
        .toList();

    var rawAbnormals = json['abnormal_values'] as List<dynamic>? ?? [];
    List<String> parsedAbnormals = rawAbnormals.map((e) => e.toString()).toList();

    PatientCondition? condition;
    if (json['patient_condition'] != null && json['patient_condition'] is Map) {
      condition = PatientCondition.fromJson(
        Map<String, dynamic>.from(json['patient_condition']),
      );
    }

    return DiagnosticReport(
      accepted: json['accepted'] == true,
      status: json['status']?.toString() ?? 'RELEVANT_MEDICAL_DOCUMENT',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.96,
      fileType: json['file_type']?.toString() ?? 'pdf',
      reason: json['reason']?.toString() ?? '',
      tests: parsedTests,
      abnormalValues: parsedAbnormals,
      patientCondition: condition,
      summary: json['summary']?.toString() ?? '',
      reportId: json['report_id']?.toString() ?? '',
    );
  }
}
