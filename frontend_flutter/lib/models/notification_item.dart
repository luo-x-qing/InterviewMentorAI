/// 通知类型
enum NotificationType { reportReady, communityReply, communityLike, system }

/// 通知数据模型
class NotificationItem {
  final String id;
  final NotificationType type;
  final String title;
  final String body;
  final DateTime timestamp;
  bool isRead;
  final String? targetRoute;
  final String? targetId;

  NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.timestamp,
    this.isRead = false,
    this.targetRoute,
    this.targetId,
  });
}
