import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

/// 统一段落标题组件（label + headline + subtitle 三段式）
/// 提取自 home_page + report_page 标题区模式
class SectionHeader extends StatelessWidget {
  final String? label;
  final String title;
  final String? subtitle;
  final EdgeInsetsGeometry padding;

  const SectionHeader({
    super.key,
    this.label,
    required this.title,
    this.subtitle,
    this.padding = const EdgeInsets.symmetric(horizontal: 4),
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (label != null) ...[
            Text(label!,
                style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.2,
                    color: AppTheme.brand500)),
            const SizedBox(height: 8),
          ],
          Text(title,
              style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                  letterSpacing: -0.03)),
          if (subtitle != null) ...[
            const SizedBox(height: 6),
            Text(subtitle!,
                style: const TextStyle(
                    fontSize: 14, color: AppTheme.textSecondary)),
          ],
        ],
      ),
    );
  }
}
