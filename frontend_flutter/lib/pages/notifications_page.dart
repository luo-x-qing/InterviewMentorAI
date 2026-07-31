import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/utils/helpers.dart';
import 'package:frontend_flutter/models/notification_item.dart';
import 'package:frontend_flutter/data/mock_notifications.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  late List<NotificationItem> _notifications;

  @override
  void initState() {
    super.initState();
    _notifications = List.from(mockNotifications);
  }

  int get _unreadCount => _notifications.where((n) => !n.isRead).length;

  void _markAllAsRead() {
    setState(() {
      for (final n in _notifications) { n.isRead = true; }
    });
  }

  void _clearAll() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('清空通知'),
        content: const Text('确定要清空所有通知吗？此操作不可撤销。'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          TextButton(
            onPressed: () {
              setState(() => _notifications.clear());
              Navigator.pop(ctx);
            },
            style: TextButton.styleFrom(foregroundColor: AppTheme.error),
            child: const Text('清空'),
          ),
        ],
      ),
    );
  }

  void _onTap(NotificationItem item) {
    setState(() => item.isRead = true);
    // 实际跳转逻辑（后续接入路由）
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        title: const Text('通知'),
        actions: [
          if (_notifications.isNotEmpty) ...[
            if (_unreadCount > 0)
              TextButton(
                onPressed: _markAllAsRead,
                child: const Text('全部已读', style: TextStyle(fontSize: 13)),
              ),
            TextButton(
              onPressed: _clearAll,
              child: const Text('清空',
                  style: TextStyle(fontSize: 13, color: AppTheme.error)),
            ),
          ],
        ],
      ),
      body: _notifications.isEmpty
          ? EmptyStateWidget(
              icon: Icons.notifications_none,
              title: '暂无通知',
              subtitle: '面试报告更新和互动消息将显示在这里',
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              itemCount: _notifications.length,
              itemBuilder: (context, index) {
                return _NotificationTile(
                  item: _notifications[index],
                  onTap: () => _onTap(_notifications[index]),
                );
              },
            ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final NotificationItem item;
  final VoidCallback onTap;

  const _NotificationTile({required this.item, required this.onTap});

  Widget _buildLeading() {
    final (icon, iconColor, bgColor) = switch (item.type) {
      NotificationType.reportReady => (
          Icons.description_outlined,
          AppTheme.brand500,
          AppTheme.brand50
        ),
      NotificationType.communityReply => (
          Icons.chat_bubble_outline,
          AppTheme.success,
          AppTheme.successBg
        ),
      NotificationType.communityLike => (
          Icons.favorite_border,
          AppTheme.purple500,
          AppTheme.purple400.withValues(alpha: 0.15)
        ),
      NotificationType.system => (
          Icons.info_outline,
          AppTheme.warning,
          AppTheme.warningBg
        ),
    };

    return Container(
      width: 40, height: 40,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(icon, color: iconColor, size: 20),
    );
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: item.isRead ? AppTheme.bgCard : AppTheme.brand50.withValues(alpha: 0.3),
          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLeading(),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(item.title,
                            style: TextStyle(
                                fontSize: 14,
                                fontWeight: item.isRead
                                    ? FontWeight.w400 : FontWeight.w600,
                                color: AppTheme.textPrimary)),
                      ),
                      if (!item.isRead)
                        Container(
                          width: 8, height: 8,
                          decoration: const BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppTheme.brand500,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(item.body,
                      maxLines: 2, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary, height: 1.4)),
                  const SizedBox(height: 6),
                  Text(AppHelpers.relativeTime(item.timestamp),
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
