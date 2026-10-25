import 'package:flutter/material.dart';

class EcgPainter extends CustomPainter {
  final List<double> points;
  final Color traceColor;
  final Color gridColor;

  EcgPainter({
    required this.points,
    this.traceColor = const Color(0xFF16A34A),
    this.gridColor = const Color(0x1A16A34A),
  });

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.width;
    final height = size.height;

    // 1. Draw hospital monitor gridlines
    final gridPaint = Paint()
      ..color = gridColor
      ..strokeWidth = 0.8
      ..style = PaintingStyle.stroke;

    const double step = 20.0;
    for (double x = 0; x <= width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, height), gridPaint);
    }
    for (double y = 0; y <= height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(width, y), gridPaint);
    }

    if (points.isEmpty) return;

    // 2. Draw cardiac plethysmogram waveform with outer glow
    final glowPaint = Paint()
      ..color = traceColor.withValues(alpha: 0.35)
      ..strokeWidth = 4.0
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;

    final corePaint = Paint()
      ..color = traceColor
      ..strokeWidth = 2.0
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;

    final path = Path();
    final double dx = width / (points.length > 1 ? (points.length - 1) : 1);

    for (int i = 0; i < points.length; i++) {
      // points are normalized between -1.0 and 1.0; 0 is center
      final double normalized = points[i].clamp(-1.0, 1.0);
      final double y = (height / 2) - (normalized * (height * 0.42));
      final double x = i * dx;

      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    // Draw the glow layer first, then the sharp core trace
    canvas.drawPath(path, glowPaint);
    canvas.drawPath(path, corePaint);

    // Draw lead point head (current sweep position)
    if (points.isNotEmpty) {
      final lastIndex = points.length - 1;
      final double lastNorm = points[lastIndex].clamp(-1.0, 1.0);
      final double headX = lastIndex * dx;
      final double headY = (height / 2) - (lastNorm * (height * 0.42));

      final headGlow = Paint()
        ..color = traceColor.withValues(alpha: 0.5)
        ..style = PaintingStyle.fill;
      final headDot = Paint()
        ..color = Colors.white
        ..style = PaintingStyle.fill;

      canvas.drawCircle(Offset(headX, headY), 5.0, headGlow);
      canvas.drawCircle(Offset(headX, headY), 2.5, headDot);
    }
  }

  @override
  bool shouldRepaint(covariant EcgPainter oldDelegate) {
    return true;
  }
}
