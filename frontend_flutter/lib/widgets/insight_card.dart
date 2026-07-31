import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

/// 优势亮点 / 改进建议卡片（提取自 home_page + report_page 重复代码）
class InsightCard extends StatelessWidget {
  final String title;
  final List<String> items;
  final List<String> tags;
  final bool isStrength;

  const InsightCard({
    super.key,
    required this.title,
    required this.items,
    required this.tags,
    required this.isStrength,
  });

  @override
  Widget build(BuildContext context) {
    final iconColor = isStrength ? AppTheme.success : AppTheme.warning;
    final iconBg = isStrength ? AppTheme.successBg : AppTheme.warningBg;
    final iconText = isStrength ? '+' : '!';

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                  isStrength ? Icons.favorite : Icons.trending_up,
                  color: iconColor,
                  size: 18),
              const SizedBox(width: 6),
              Text(title,
                  style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          ...items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 20,
                      height: 20,
                      decoration: BoxDecoration(
                        color: iconBg,
                        borderRadius: BorderRadius.circular(5),
                      ),
                      child: Center(
                        child: Text(iconText,
                            style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: iconColor)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(item,
                          style: const TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                              height: 1.5)),
                    ),
                  ],
                ),
              )),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: tags
                .map((tag) => Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.bgPage,
                        borderRadius:
                            BorderRadius.circular(AppTheme.radiusFull),
                      ),
                      child: Text(tag,
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.textSecondary)),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }
}
