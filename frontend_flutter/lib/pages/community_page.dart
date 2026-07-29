import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

class CommunityPage extends StatelessWidget {
  const CommunityPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('社区')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.group, size: 64, color: AppTheme.textMuted.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            const Text('面试社区',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            const Text('与求职者交流面试经验',
                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
