import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/ecg_painter.dart';

class DashboardScreen extends StatelessWidget {
  final Function(int) onNavigateToTab;

  const DashboardScreen({super.key, required this.onNavigateToTab});

  static const List<double> miniEcgPoints = [
    0.0, 0.0, 0.05, -0.05, 0.0, 0.15, -0.3, 0.85, -0.4, 0.2, 0.0, 0.05, 0.0,
    0.0, 0.0, 0.05, -0.05, 0.0, 0.15, -0.3, 0.85, -0.4, 0.2, 0.0, 0.05, 0.0,
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.lightBg,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppTheme.primaryGreen.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.monitor_heart_rounded,
                color: AppTheme.primaryGreen,
                size: 22,
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'PranaScan AI',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textDark,
                      ),
                ),
                Text(
                  'Clinical Diagnostics & Telemetry',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontSize: 11,
                        color: AppTheme.textMuted,
                      ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Privacy Protocol Banner
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: AppTheme.darkGreen,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppTheme.tealAccent,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'CLINICAL TELEMETRY ACTIVE · Zero Cloud Retention',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'HIPAA',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Patient Telemetry HUD Card
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF071A10),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF14532D)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.15),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: const BoxDecoration(
                              color: AppTheme.tealAccent,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text(
                            'PATIENT HUD · PX-7704',
                            style: TextStyle(
                              color: Color(0xFF86EFAC),
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.6,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF16A34A).withValues(alpha: 0.25),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.5)),
                        ),
                        child: const Text(
                          'TELEMETRY LOCKED',
                          style: TextStyle(
                            color: Color(0xFF4ADE80),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Vitals row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildVitalMetric(
                        icon: '♥',
                        label: 'HEART RATE',
                        value: '72',
                        unit: 'BPM',
                        subtext: 'Normal Sinus',
                        color: const Color(0xFFEF4444),
                      ),
                      Container(width: 1, height: 42, color: Colors.white12),
                      _buildVitalMetric(
                        icon: '⚪',
                        label: 'SpO2 PULSE',
                        value: '98',
                        unit: '%',
                        subtext: 'Arterial Sat',
                        color: const Color(0xFF10B981),
                      ),
                      Container(width: 1, height: 42, color: Colors.white12),
                      _buildVitalMetric(
                        icon: '⚡',
                        label: 'NIBP',
                        value: '120/80',
                        unit: 'mmHg',
                        subtext: 'Optimal',
                        color: const Color(0xFF38BDF8),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Mini ECG Waveform preview
                  Container(
                    height: 50,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: const Color(0xFF04160B),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0x2216A34A)),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: CustomPaint(
                      painter: EcgPainter(
                        points: miniEcgPoints,
                        traceColor: const Color(0xFF22C55E),
                        gridColor: const Color(0x0F22C55E),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Diagnostic Modules Section Title
            Text(
              'Diagnostic Suites',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textDark,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              'Touch a clinical module to launch triage or monitoring',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontSize: 12,
                    color: AppTheme.textMuted,
                  ),
            ),
            const SizedBox(height: 12),

            // Module Cards Grid
            _buildModuleCard(
              context: context,
              icon: Icons.document_scanner_rounded,
              iconColor: const Color(0xFF059669),
              code: 'MOD-01',
              title: 'Document Validation & Intake',
              description:
                  'Multi-stage verification for diagnostic PDFs, laboratory scans, and clinical prescriptions.',
              actionText: 'Launch Intake Validator',
              onTap: () => onNavigateToTab(1),
            ),
            const SizedBox(height: 10),

            _buildModuleCard(
              context: context,
              icon: Icons.table_chart_rounded,
              iconColor: const Color(0xFF0284C7),
              code: 'MOD-02',
              title: 'Biochemical Lab Reader',
              description:
                  'Extract hematology & metabolic parameters with reference intervals and patient condition scoring.',
              actionText: 'Extract Lab Parameters',
              onTap: () => onNavigateToTab(2),
            ),
            const SizedBox(height: 10),

            _buildModuleCard(
              context: context,
              icon: Icons.smart_toy_rounded,
              iconColor: const Color(0xFF2563EB),
              code: 'MOD-03',
              title: 'Grounded Medical Assistant',
              description:
                  'Consult clinical AI anchored in validated lab findings without fabricated values.',
              actionText: 'Open Clinical Copilot',
              onTap: () => onNavigateToTab(3),
            ),
            const SizedBox(height: 10),

            _buildModuleCard(
              context: context,
              icon: Icons.favorite_rounded,
              iconColor: const Color(0xFFDC2626),
              code: 'MOD-04',
              title: 'Cardiac Telemetry & rPPG',
              description:
                  'Contactless facial capillary pulse wave extraction, 60 FPS oscilloscope & rhythm simulation.',
              actionText: 'Start Cardiac Monitor',
              onTap: () => onNavigateToTab(4),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildVitalMetric({
    required String icon,
    required String label,
    required String value,
    required String unit,
    required String subtext,
    required Color color,
  }) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 9,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(width: 3),
            Text(
              unit,
              style: TextStyle(
                color: color,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          subtext,
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 9,
          ),
        ),
      ],
    );
  }

  Widget _buildModuleCard({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required String code,
    required String title,
    required String description,
    required String actionText,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.borderSubtle),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: iconColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: iconColor, size: 20),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.lightBg,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppTheme.borderSubtle),
                  ),
                  child: Text(
                    code,
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              title,
              style: const TextStyle(
                color: AppTheme.textDark,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              description,
              style: TextStyle(
                color: AppTheme.textMuted,
                fontSize: 12,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Text(
                  actionText,
                  style: TextStyle(
                    color: AppTheme.primaryGreen,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(
                  Icons.arrow_forward_rounded,
                  size: 14,
                  color: AppTheme.primaryGreen,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
