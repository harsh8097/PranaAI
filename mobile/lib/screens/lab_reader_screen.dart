import 'package:flutter/material.dart';
import '../models/diagnostic_report.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class LabReaderScreen extends StatefulWidget {
  final DiagnosticReport? currentReport;
  final Function(DiagnosticReport) onConsultCopilot;

  const LabReaderScreen({
    super.key,
    this.currentReport,
    required this.onConsultCopilot,
  });

  @override
  State<LabReaderScreen> createState() => _LabReaderScreenState();
}

class _LabReaderScreenState extends State<LabReaderScreen> {
  DiagnosticReport? report;
  bool isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.currentReport != null) {
      report = widget.currentReport;
    } else {
      _loadDefaultReport();
    }
  }

  @override
  void didUpdateWidget(covariant LabReaderScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.currentReport != null && widget.currentReport != report) {
      setState(() {
        report = widget.currentReport;
      });
    }
  }

  Future<void> _loadDefaultReport() async {
    setState(() => isLoading = true);
    final rep = await ApiService.validateDocument(fileName: 'sample_medical_cbc_report.pdf');
    setState(() {
      report = rep;
      isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.lightBg,
      appBar: AppBar(
        title: const Text('Biochemical Lab Reader'),
        actions: [
          IconButton(
            tooltip: 'Reload Sample Data',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadDefaultReport,
          ),
        ],
      ),
      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(color: AppTheme.primaryGreen),
            )
          : report == null
              ? _buildEmptyState()
              : SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Active Document Forwarded Banner
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF4),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFF86EFAC)),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: AppTheme.primaryGreen,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'ACTIVE CLINICAL REPORT',
                                    style: TextStyle(
                                      color: Color(0xFF166534),
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                  Text(
                                    report!.reportId,
                                    style: const TextStyle(
                                      color: Color(0xFF14532D),
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      fontFamily: 'monospace',
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                '✓ Authenticated',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Patient Condition Assessment Card
                      if (report!.patientCondition != null) ...[
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFFBEB),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xFFFCD34D)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFD97706).withValues(alpha: 0.15),
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      report!.patientCondition!.badge,
                                      style: const TextStyle(
                                        color: Color(0xFFB45309),
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              Text(
                                report!.patientCondition!.summary,
                                style: const TextStyle(
                                  color: Color(0xFF78350F),
                                  fontSize: 13,
                                  height: 1.45,
                                ),
                              ),
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: const Color(0xFFFDE68A)),
                                ),
                                child: const Row(
                                  children: [
                                    Icon(Icons.medical_services_outlined,
                                        color: Color(0xFFD97706), size: 16),
                                    SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        'Grounded in validated reference intervals. Clinical review recommended.',
                                        style: TextStyle(
                                          color: Color(0xFF92400E),
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 18),
                      ],

                      // Parameter Extraction Summary
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Extracted Lab Biomarkers',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textDark,
                                ),
                          ),
                          Text(
                            '${report!.tests.length} Parameters',
                            style: TextStyle(
                              color: AppTheme.textMuted,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),

                      // Test Items List
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: report!.tests.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final item = report!.tests[index];
                          final isAbnormal = item.isAbnormal;

                          return Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: isAbnormal
                                    ? const Color(0xFFFCA5A5)
                                    : AppTheme.borderSubtle,
                                width: isAbnormal ? 1.2 : 1.0,
                              ),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        item.label,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          fontSize: 13,
                                          color: AppTheme.textDark,
                                        ),
                                      ),
                                      const SizedBox(height: 3),
                                      Text(
                                        'Reference Interval: ${item.referenceRange}',
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: AppTheme.textMuted,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Row(
                                      children: [
                                        Text(
                                          item.value,
                                          style: TextStyle(
                                            fontSize: 15,
                                            fontWeight: FontWeight.w800,
                                            color: isAbnormal
                                                ? AppTheme.alertDanger
                                                : AppTheme.primaryGreen,
                                          ),
                                        ),
                                        const SizedBox(width: 3),
                                        Text(
                                          item.unit,
                                          style: TextStyle(
                                            fontSize: 10,
                                            fontWeight: FontWeight.w600,
                                            color: AppTheme.textMuted,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: isAbnormal
                                            ? AppTheme.alertDangerBg
                                            : AppTheme.alertSuccessBg,
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        isAbnormal ? 'OUTSIDE INTERVAL' : 'NORMAL',
                                        style: TextStyle(
                                          color: isAbnormal
                                              ? AppTheme.alertDanger
                                              : AppTheme.primaryGreen,
                                          fontSize: 9,
                                          fontWeight: FontWeight.w800,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 20),

                      // Consult AI Copilot Banner Button
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            widget.onConsultCopilot(report!);
                          },
                          icon: const Icon(Icons.smart_toy_rounded, size: 18),
                          label: const Text(
                            'Ask Grounded Clinical Assistant (Module 03)',
                            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF1D4ED8),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.description_outlined, size: 48, color: Colors.grey),
          const SizedBox(height: 12),
          const Text(
            'No Report Extracted Yet',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _loadDefaultReport,
            child: const Text('Load Sample Clinical Report'),
          ),
        ],
      ),
    );
  }
}
