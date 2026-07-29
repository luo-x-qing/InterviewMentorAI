import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('通知')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.notifications_none, size: 64,
                color: AppTheme.textMuted.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            const Text('暂无通知',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            const Text('面试报告更新和消息将显示在这里',
                style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          ],
        ),
      ),
    );
  }
}
