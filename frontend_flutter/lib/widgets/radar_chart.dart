import 'dart:math';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

/// 面试能力维度雷达图（提取自 home_page + report_page 重复代码）
class RadarChart extends StatelessWidget {
  final List<double> values; // 0.0 ~ 1.0
  final List<String>? labels;

  const RadarChart({super.key, required this.values, this.labels});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return CustomPaint(
          size: Size(constraints.maxWidth, constraints.maxHeight),
          painter: _RadarPainter(
            values,
            labels ?? const [
              '表达清晰度', '技术深度', '逻辑思维',
              '沟通能力', '应变能力', '专业知识',
            ],
          ),
        );
      },
    );
  }
}

class _RadarPainter extends CustomPainter {
  final List<double> values;
  final List<String> labels;

  _RadarPainter(this.values, this.labels);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 22;
    final n = values.length;
    final angleStep = 2 * pi / n;

    final gridPaint = Paint()
      ..color = AppTheme.borderLight
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // 网格环
    for (int ring = 1; ring <= 5; ring++) {
      final r = radius * ring / 5;
      final path = Path();
      for (int i = 0; i < n; i++) {
        final angle = -pi / 2 + i * angleStep;
        final x = center.dx + r * cos(angle);
        final y = center.dy + r * sin(angle);
        i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
      }
      path.close();
      canvas.drawPath(path, gridPaint);
    }

    // 轴线
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      canvas.drawLine(
        center,
        Offset(center.dx + radius * cos(angle),
            center.dy + radius * sin(angle)),
        gridPaint,
      );
    }

    // 数据填充
    final dataPaint = Paint()
      ..color = AppTheme.brand500.withValues(alpha: 0.12)
      ..style = PaintingStyle.fill;
    final dataBorder = Paint()
      ..color = AppTheme.brand500
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;
    final dataPath = Path();
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * (i < values.length ? values[i].clamp(0.0, 1.0) : 0.0);
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      i == 0 ? dataPath.moveTo(x, y) : dataPath.lineTo(x, y);
    }
    dataPath.close();
    canvas.drawPath(dataPath, dataPaint);
    canvas.drawPath(dataPath, dataBorder);

    // 数据点
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * (i < values.length ? values[i].clamp(0.0, 1.0) : 0.0);
      final pt = Offset(center.dx + r * cos(angle),
          center.dy + r * sin(angle));
      canvas.drawCircle(pt, 5, Paint()..color = AppTheme.brand500);
      canvas.drawCircle(pt, 2.5, Paint()..color = Colors.white);
    }

    // 标签
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final x = center.dx + (radius + 20) * cos(angle);
      final y = center.dy + (radius + 20) * sin(angle);
      final tp = TextPainter(
        text: TextSpan(
          text: i < labels.length ? labels[i] : '',
          style: const TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 11,
            fontWeight: FontWeight.w500,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) =>
      old.values != values || old.labels != labels;
}
