import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/coach_service.dart';

/// 结课报告页：正确率 + 弱项标签 + 建议（真实 coach 结课数据）
class CoachReportPage extends StatelessWidget {
  final CoachSessionReportData report;

  const CoachReportPage({super.key, required this.report});

  @override
  Widget build(BuildContext context) {
    final accuracy = report.accuracy;
    final score = (accuracy * 100).round();
    final grade = _grade(score);

    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        title: const Text('结课报告'),
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context, false),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: AppTheme.cardDecoration,
            child: Column(
              children: [
                const Text('本轮陪练',
                    style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                const SizedBox(height: 8),
                Text('$score',
                    style: const TextStyle(fontSize: 56, fontWeight: FontWeight.w600,
                        color: AppTheme.brand500, height: 1)),
                Container(
                  margin: const EdgeInsets.only(top: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.brand50,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                  ),
                  child: Text(grade,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
                          color: AppTheme.brand500)),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _statItem('${report.totalQuestions}', '题目'),
                    Container(width: 1, height: 32, color: AppTheme.borderLight),
                    _statItem('${report.correctAnswers}', '答对'),
                    Container(width: 1, height: 32, color: AppTheme.borderLight),
                    _statItem('${(accuracy * 100).toStringAsFixed(0)}%', '正确率'),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          const Text('待加强知识点',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 10),
          if (report.weaknesses.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.bgCard,
                borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: const Text('本轮未发现明显弱项，继续保持。',
                  style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final w in report.weaknesses)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.warningBg,
                      borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                      border: Border.all(color: AppTheme.warning.withValues(alpha: 0.3)),
                    ),
                    child: Text(w,
                        style: const TextStyle(fontSize: 13,
                            fontWeight: FontWeight.w500, color: AppTheme.warning)),
                  ),
              ],
            ),
          const SizedBox(height: 24),
          if (report.suggestions.isNotEmpty) ...[
            const Text('后续建议',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.brand50,
                borderRadius: BorderRadius.circular(AppTheme.radiusLg),
                border: Border.all(color: AppTheme.brand100),
              ),
              child: Text(report.suggestions,
                  style: const TextStyle(fontSize: 14,
                      color: AppTheme.textSecondary, height: 1.7)),
            ),
          ],
          const SizedBox(height: 28),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => Navigator.pop(context, true),
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('再来一轮'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statItem(String value, String label) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(value,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary)),
        const SizedBox(height: 2),
        Text(label,
            style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
      ],
    );
  }

  static String _grade(int score) {
    if (score >= 90) return '卓越';
    if (score >= 80) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 60) return '一般';
    return '待提高';
  }
}