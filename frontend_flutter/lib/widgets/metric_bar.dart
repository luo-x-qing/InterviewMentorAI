import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

/// 能力维度评分条（提取自 home_page + report_page 重复代码）
class MetricBar extends StatelessWidget {
  final String label;
  final int value; // 0-100
  final Color? color;

  const MetricBar({
    super.key,
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final barColor = color ?? AppTheme.brand500;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary)),
              Text('$value',
                  style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 5),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: value.clamp(0, 100) / 100,
              minHeight: 5,
              backgroundColor: AppTheme.borderLight,
              valueColor: AlwaysStoppedAnimation(barColor),
            ),
          ),
        ],
      ),
    );
  }
}
