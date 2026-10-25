import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/ecg_painter.dart';

enum RhythmType { normal, tachycardia, bradycardia, arrhythmia }

class CardiacMonitorScreen extends StatefulWidget {
  const CardiacMonitorScreen({super.key});

  @override
  State<CardiacMonitorScreen> createState() => _CardiacMonitorScreenState();
}

class _CardiacMonitorScreenState extends State<CardiacMonitorScreen>
    with SingleTickerProviderStateMixin {
  bool isMonitoring = true;
  RhythmType currentRhythm = RhythmType.normal;
  int currentBpm = 72;
  String rhythmLabel = 'Normal Sinus Rhythm';
  String healthState = 'Normal Physiological State';
  String clinicalAdvice =
      'Resting cardiovascular tone is within target adult limits (60–100 BPM). Normal ventricular repolarization observed.';

  late AnimationController _pulseController;
  Timer? _waveformTimer;
  final List<double> _waveformPoints = List.filled(120, 0.0);
  double _timePhase = 0.0;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 830), // ~72 BPM
    )..repeat(reverse: true);

    _startOscilloscope();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _waveformTimer?.cancel();
    super.dispose();
  }

  void _startOscilloscope() {
    _waveformTimer?.cancel();
    _waveformTimer = Timer.periodic(const Duration(milliseconds: 33), (timer) {
      if (!isMonitoring) return;

      setState(() {
        _timePhase += 0.12;

        // Generate synthetic ECG P-Q-R-S-T / Pleth wave based on active rhythm
        double waveVal = 0.0;
        final phaseMod = _timePhase % (2 * math.pi);

        if (currentRhythm == RhythmType.arrhythmia) {
          // Irregular interval jitter
          final jitter = math.sin(_timePhase * 0.7) * 0.3;
          waveVal = math.sin(phaseMod) * 0.25 + jitter;
          if (phaseMod > 1.2 && phaseMod < 1.4) {
            waveVal = 0.85; // R-peak
          } else if (phaseMod >= 1.4 && phaseMod < 1.5) {
            waveVal = -0.35; // S-wave
          }
        } else {
          // Standard P-Q-R-S-T morphological trace
          if (phaseMod < 0.3) {
            waveVal = math.sin(phaseMod * math.pi / 0.3) * 0.12; // P wave
          } else if (phaseMod >= 0.3 && phaseMod < 0.45) {
            waveVal = -0.08; // Q dip
          } else if (phaseMod >= 0.45 && phaseMod < 0.6) {
            waveVal = 0.95; // Sharp R peak
          } else if (phaseMod >= 0.6 && phaseMod < 0.75) {
            waveVal = -0.38; // S drop
          } else if (phaseMod >= 0.75 && phaseMod < 1.4) {
            final tPhase = (phaseMod - 0.75) / 0.65;
            waveVal = math.sin(tPhase * math.pi) * 0.24; // T wave
          } else {
            waveVal = 0.0; // Isoelectric baseline
          }
        }

        // Add subtle physiological noise
        waveVal += (math.Random().nextDouble() - 0.5) * 0.04;

        _waveformPoints.removeAt(0);
        _waveformPoints.add(waveVal);
      });
    });
  }

  void _setRhythm(RhythmType type) {
    setState(() {
      currentRhythm = type;
      switch (type) {
        case RhythmType.normal:
          currentBpm = 72;
          rhythmLabel = 'Normal Sinus Rhythm';
          healthState = 'Optimal Hemodynamics';
          clinicalAdvice =
              'Resting cardiovascular tone is within target adult limits (60–100 BPM). Normal ventricular repolarization observed.';
          _pulseController.duration = const Duration(milliseconds: 833);
          break;
        case RhythmType.tachycardia:
          currentBpm = 114;
          rhythmLabel = 'Sinus Tachycardia';
          healthState = 'Elevated Pulse Rate';
          clinicalAdvice =
              'Heart rate exceeds resting threshold (>100 BPM). Potential correlates: physical exertion, caffeine, acute stress, or dehydration.';
          _pulseController.duration = const Duration(milliseconds: 526);
          break;
        case RhythmType.bradycardia:
          currentBpm = 48;
          rhythmLabel = 'Sinus Bradycardia';
          healthState = 'Sub-baseline Pulse Rate';
          clinicalAdvice =
              'Heart rate is below standard resting baseline (<60 BPM). Typical in well-conditioned endurance athletes or vagal tone elevation.';
          _pulseController.duration = const Duration(milliseconds: 1250);
          break;
        case RhythmType.arrhythmia:
          currentBpm = 88;
          rhythmLabel = 'Arrhythmia / PVC Complex';
          healthState = 'Variable Rhythm Morphology';
          clinicalAdvice =
              'Irregular inter-beat intervals (R-R variability fluctuation). Advised to verify via 12-lead diagnostic ECG.';
          _pulseController.duration = const Duration(milliseconds: 681);
          break;
      }
      _pulseController.repeat(reverse: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.lightBg,
      appBar: AppBar(
        title: const Text('Cardiac Telemetry & rPPG'),
        actions: [
          IconButton(
            tooltip: isMonitoring ? 'Pause Telemetry' : 'Resume Telemetry',
            icon: Icon(isMonitoring ? Icons.pause_circle_outline : Icons.play_circle_outline),
            onPressed: () {
              setState(() => isMonitoring = !isMonitoring);
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Camera ROI Forehead Viewfinder Simulation
            Container(
              height: 160,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Stack(
                children: [
                  // Center Forehead ROI Guide
                  Center(
                    child: Container(
                      width: 140,
                      height: 90,
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: AppTheme.tealAccent.withValues(alpha: 0.8),
                          width: 1.5,
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.face_retouching_natural_rounded,
                            color: AppTheme.tealAccent.withValues(alpha: 0.7),
                            size: 32,
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'ALIGN FOREHEAD ROI',
                            style: TextStyle(
                              color: Color(0xFF34D399),
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Top live telemetry overlay tag
                  Positioned(
                    top: 10,
                    left: 12,
                    child: Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: isMonitoring ? const Color(0xFF22C55E) : Colors.amber,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          isMonitoring ? 'LIVE rPPG CAPTURE' : 'TELEMETRY PAUSED',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),

                  Positioned(
                    bottom: 10,
                    right: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.black45,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'Bandpass: 0.7–3.0 Hz',
                        style: TextStyle(color: Colors.white70, fontSize: 9),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Live Pulse Reading Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.borderSubtle),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.02),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'ESTIMATED ARTERIAL HEART RATE',
                        style: TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.alertSuccessBg,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF86EFAC)),
                        ),
                        child: Text(
                          rhythmLabel,
                          style: const TextStyle(
                            color: Color(0xFF166534),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),

                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      ScaleTransition(
                        scale: Tween<double>(begin: 0.88, end: 1.18).animate(
                          CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
                        ),
                        child: const Icon(
                          Icons.favorite_rounded,
                          color: Color(0xFFDC2626),
                          size: 36,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '$currentBpm',
                        style: const TextStyle(
                          color: AppTheme.textDark,
                          fontSize: 44,
                          fontWeight: FontWeight.w900,
                          height: 1.0,
                        ),
                      ),
                      const SizedBox(width: 6),
                      const Padding(
                        padding: EdgeInsets.only(top: 14),
                        child: Text(
                          'BPM',
                          style: TextStyle(
                            color: AppTheme.textMuted,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Hospital-Grade Oscilloscope Screen
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFF04160B),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF0F3A1E)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.2),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFF16A34A),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text(
                              'PLETH / rPPG',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Sos-Butterworth (0.7–3.0 Hz)',
                            style: TextStyle(color: Colors.white54, fontSize: 10),
                          ),
                        ],
                      ),
                      const Text(
                        'SWEEP: 25 mm/s · 60 FPS',
                        style: TextStyle(
                          color: Color(0xFF4ADE80),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),

                  // Waveform Canvas
                  Container(
                    height: 110,
                    width: double.infinity,
                    clipBehavior: Clip.antiAlias,
                    decoration: BoxDecoration(
                      color: const Color(0xFF020E06),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: CustomPaint(
                      painter: EcgPainter(
                        points: _waveformPoints,
                        traceColor: const Color(0xFF22C55E),
                        gridColor: const Color(0x1A22C55E),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Patient Cardiovascular Condition Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderSubtle),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF4),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: const Color(0xFF86EFAC)),
                        ),
                        child: Text(
                          healthState,
                          style: const TextStyle(
                            color: Color(0xFF15803D),
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    clinicalAdvice,
                    style: TextStyle(
                      color: AppTheme.textMuted,
                      fontSize: 12,
                      height: 1.45,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Simulation Rhythm Switcher
            Text(
              'Simulate Clinical Cardiac Rhythms',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textDark,
                  ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildRhythmButton(
                  title: 'Normal (72 BPM)',
                  type: RhythmType.normal,
                ),
                _buildRhythmButton(
                  title: 'Tachycardia (114 BPM)',
                  type: RhythmType.tachycardia,
                ),
                _buildRhythmButton(
                  title: 'Bradycardia (48 BPM)',
                  type: RhythmType.bradycardia,
                ),
                _buildRhythmButton(
                  title: 'Arrhythmia (88 BPM)',
                  type: RhythmType.arrhythmia,
                ),
              ],
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildRhythmButton({
    required String title,
    required RhythmType type,
  }) {
    final isSelected = currentRhythm == type;
    return ChoiceChip(
      label: Text(
        title,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: isSelected ? Colors.white : AppTheme.textDark,
        ),
      ),
      selected: isSelected,
      selectedColor: AppTheme.primaryGreen,
      backgroundColor: Colors.white,
      side: BorderSide(
        color: isSelected ? AppTheme.primaryGreen : AppTheme.borderSubtle,
      ),
      onSelected: (val) {
        if (val) _setRhythm(type);
      },
    );
  }
}
