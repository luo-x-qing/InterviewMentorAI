import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend_flutter/theme.dart';

class ReportPage extends StatelessWidget {
  const ReportPage({super.key});

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments;
    final data = args as Map<String, dynamic>?;
    final reportContent = data?['report'] as String? ?? '暂无分析内容';

    return Scaffold(
      appBar: AppBar(
        title: const Text('面试复盘报告'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            const Text('评估报告',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                    letterSpacing: 1.2, color: AppTheme.brand500)),
            const SizedBox(height: 8),
            const Text('面试表现分析',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 4),
            const Text('基于 AI 多维评估模型，全面分析你的面试表现',
                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
            const SizedBox(height: 24),

            // Dashboard grid
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  flex: 3,
                  child: _buildRadarCard(),
                ),
                const SizedBox(width: 20),
                Expanded(
                  flex: 4,
                  child: Column(
                    children: [
                      _buildScoreCard(),
                      const SizedBox(height: 16),
                      _buildInsightRow(),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 28),

            // Full report markdown
            if (reportContent.isNotEmpty && reportContent != '暂无分析内容') ...[
              const Text('详细分析报告',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary)),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: AppTheme.cardDecoration,
                child: Markdown(
                  data: reportContent,
                  styleSheet: MarkdownStyleSheet(
                    h1: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary),
                    h2: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary),
                    p: const TextStyle(fontSize: 14, color: AppTheme.textSecondary,
                        height: 1.6),
                  ),
                ),
              ),
            ],
          ],
          const SizedBox(height: 28),
          const Divider(),
        ),
      ),
    );
  }

  Widget _buildRadarCard() {
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: AppTheme.cardDecoration,
      child: Column(
        children: [
          const Text('能力维度雷达图',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 20),
          SizedBox(
            height: 300,
            child: _RadarChart(values: [0.88, 0.82, 0.90, 0.85, 0.78, 0.86]),
          ),
        ],
      ),
    );
  }

  Widget _buildScoreCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(28),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Text('85',
                  style: TextStyle(fontSize: 56, fontWeight: FontWeight.w600,
                      color: AppTheme.brand500, height: 1)),
              const Text(' /100',
                  style: TextStyle(fontSize: 16, color: AppTheme.textMuted)),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.brand50,
                  borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                ),
                child: const Text('优秀',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
                        color: AppTheme.brand500)),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _metricBar('表达清晰度', 88),
          _metricBar('技术深度', 82),
          _metricBar('逻辑思维', 90),
          _metricBar('沟通能力', 85),
          _metricBar('应变能力', 78),
        ],
      ),
    );
  }

  Widget _metricBar(String label, int value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
              Text('$value', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 5),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: value / 100,
              minHeight: 5,
              backgroundColor: AppTheme.borderLight,
              valueColor: const AlwaysStoppedAnimation(AppTheme.brand500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInsightRow() {
    return Row(
      children: [
        Expanded(child: _insightCard(
          '💪 优势亮点',
          ['逻辑结构清晰，使用 STAR 法则组织回答',
           '技术深度突出，结合真实项目经验',
           '表达流畅自信，语速适中'],
          isStrength: true,
          tags: const ['架构思维', 'STAR 法则', '表达力'],
        )),
        const SizedBox(width: 16),
        Expanded(child: _insightCard(
          '🎯 改进建议',
          ['用数据支撑观点，展示定量分析思路',
           '部分技术描述可更简洁，避免冗长'],
          isStrength: false,
          tags: const ['数据思维', '简洁表达'],
        )),
      ],
    );
  }

  Widget _insightCard(String title, List<String> items,
      {required bool isStrength, required List<String> tags}) {
    final iconColor = isStrength ? AppTheme.success : AppTheme.warning;
    final iconBg = isStrength ? AppTheme.successBg : AppTheme.warningBg;
    final iconText = isStrength ? '+' : '!';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 14),
          ...items.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 22, height: 22,
                  decoration: BoxDecoration(
                    color: iconBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Center(
                    child: Text(iconText,
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                            color: iconColor)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(item,
                      style: const TextStyle(fontSize: 13,
                          color: AppTheme.textSecondary, height: 1.5)),
                ),
              ],
            ),
          )),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6, runSpacing: 6,
            children: tags.map((tag) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.bgPage,
                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
              ),
              child: Text(tag,
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500,
                      color: AppTheme.textSecondary)),
            )).toList(),
          ),
        ],
      ),
    );
  }
}

// ─── Radar Chart Painter ───
class _RadarChart extends StatelessWidget {
  final List<double> values;
  const _RadarChart({required this.values});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return CustomPaint(
          size: Size(constraints.maxWidth, constraints.maxHeight),
          painter: _RadarPainter(values),
        );
      },
    );
  }
}

class _RadarPainter extends CustomPainter {
  final List<double> values;
  _RadarPainter(this.values);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 24;
    final n = values.length;
    final angleStep = 2 * pi / n;
    final labels = ['表达清晰度', '技术深度', '逻辑思维', '沟通能力', '应变能力', '专业知识'];

    final gridPaint = Paint()
      ..color = AppTheme.borderLight
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // Grid rings
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

    // Axis lines
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      canvas.drawLine(
        center,
        Offset(center.dx + radius * cos(angle), center.dy + radius * sin(angle)),
        gridPaint,
      );
    }

    // Target ring (85)
    final targetPaint = Paint()
      ..color = AppTheme.borderMedium
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    final targetPath = Path();
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * 0.85;
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      i == 0 ? targetPath.moveTo(x, y) : targetPath.lineTo(x, y);
    }
    targetPath.close();

    // Data fill
    final dataPaint = Paint()
      ..color = AppTheme.brand500.withValues(alpha: 0.12)
      ..style = PaintingStyle.fill;
    final dataBorder = Paint()
      ..color = AppTheme.brand500
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    final dataPath = Path();
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      i == 0 ? dataPath.moveTo(x, y) : dataPath.lineTo(x, y);
    }
    dataPath.close();
    canvas.drawPath(dataPath, dataPaint);
    canvas.drawPath(dataPath, dataBorder);

    // Data dots
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final pt = Offset(center.dx + r * cos(angle), center.dy + r * sin(angle));
      canvas.drawCircle(pt, 4.5, Paint()..color = AppTheme.brand500..style = PaintingStyle.fill);
      canvas.drawCircle(pt, 2.5, Paint()..color = Colors.white..style = PaintingStyle.fill);
    }

    // Labels
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final x = center.dx + (radius + 20) * cos(angle);
      final y = center.dy + (radius + 20) * sin(angle);
      final tp = TextPainter(
        text: TextSpan(
          text: labels[i],
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 11),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) => old.values != values;
}
