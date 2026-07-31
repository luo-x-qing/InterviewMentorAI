import 'package:frontend_flutter/models/notification_item.dart';

/// 15+ 条模拟通知数据
final List<NotificationItem> mockNotifications = [
  // ── 报告完成 ──
  NotificationItem(
    id: 'n01', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"高级前端工程师"模拟面试中获得 85 分（优秀），点击查看完整评估。',
    timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
    targetRoute: '/report',
  ),
  NotificationItem(
    id: 'n02', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"全栈工程师"模拟面试中获得 72 分（良好），已发现 3 个可改进领域。',
    timestamp: DateTime.now().subtract(const Duration(hours: 3)),
    isRead: true,
  ),
  NotificationItem(
    id: 'n03', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"前端实习生"模拟面试中获得 92 分（卓越），表现非常出色！',
    timestamp: DateTime.now().subtract(const Duration(days: 1)),
    isRead: true,
  ),
  NotificationItem(
    id: 'n04', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"React 专场"模拟面试中获得 78 分（良好），技术深度维度有待加强。',
    timestamp: DateTime.now().subtract(const Duration(days: 2)),
    isRead: true,
  ),
  NotificationItem(
    id: 'n05', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"系统设计"模拟面试中获得 68 分（一般），建议重点复习分布式架构。',
    timestamp: DateTime.now().subtract(const Duration(days: 3)),
    isRead: true,
  ),

  // ── 社区回复 ──
  NotificationItem(
    id: 'n06', type: NotificationType.communityReply,
    title: '有人回复了你的帖子',
    body: '张明 回复了你："谢谢分享！这个面试经验对我帮助很大，特别是关于系统设计的部分。"',
    timestamp: DateTime.now().subtract(const Duration(hours: 2)),
    targetRoute: '/post/n06',
    targetId: 'p01',
  ),
  NotificationItem(
    id: 'n07', type: NotificationType.communityReply,
    title: '有人回复了你的帖子',
    body: '李华 在你的"前端面试高频题总结"帖子下发表了评论。',
    timestamp: DateTime.now().subtract(const Duration(hours: 6)),
    isRead: true,
    targetId: 'p03',
  ),
  NotificationItem(
    id: 'n08', type: NotificationType.communityReply,
    title: '有人回复了你的评论',
    body: '王芳 回复了你的评论："同意，Vue 3 Composition API 确实比 Options API 更灵活。"',
    timestamp: DateTime.now().subtract(const Duration(days: 1)),
    isRead: true,
    targetId: 'p02',
  ),
  NotificationItem(
    id: 'n09', type: NotificationType.communityReply,
    title: '新回复提醒',
    body: '你的帖子"从零到Offer：我的三个月前端进阶之路"获得了 5 条新回复。',
    timestamp: DateTime.now().subtract(const Duration(days: 2)),
    isRead: true,
    targetId: 'p04',
  ),

  // ── 社区点赞 ──
  NotificationItem(
    id: 'n10', type: NotificationType.communityLike,
    title: '你的帖子获得了 10 个赞',
    body: '"大厂面试官视角：我们到底在考察什么"帖子已获得 10 个赞。',
    timestamp: DateTime.now().subtract(const Duration(hours: 8)),
    targetId: 'p05',
  ),
  NotificationItem(
    id: 'n11', type: NotificationType.communityLike,
    title: '有人赞了你的评论',
    body: '你的评论"建议结合项目经验回答，更有说服力"获得 3 个赞。',
    timestamp: DateTime.now().subtract(const Duration(days: 1)),
    isRead: true,
  ),

  // ── 系统通知 ──
  NotificationItem(
    id: 'n12', type: NotificationType.system,
    title: '欢迎加入 InterviewMentorAI',
    body: '欢迎使用 AI 面试复盘助手！完成你的第一次模拟面试，获取专业评估报告。',
    timestamp: DateTime.now().subtract(const Duration(days: 7)),
    isRead: true,
  ),
  NotificationItem(
    id: 'n13', type: NotificationType.system,
    title: '新功能上线',
    body: '题库功能已上线！现在可以按分类浏览 60+ 道精选面试题，收藏感兴趣的题目并开始练习。',
    timestamp: DateTime.now().subtract(const Duration(days: 4)),
    isRead: true,
  ),
  NotificationItem(
    id: 'n14', type: NotificationType.system,
    title: '本周面试报告已更新',
    body: '系统已为你自动分析本周的表现趋势，整体评分相比上周提升了 5 分，继续保持！',
    timestamp: DateTime.now().subtract(const Duration(hours: 12)),
  ),

  // ── 额外混合 ──
  NotificationItem(
    id: 'n15', type: NotificationType.reportReady,
    title: '面试报告已生成',
    body: '你在"算法专场"模拟面试中获得 81 分（优秀），逻辑思维能力突出。',
    timestamp: DateTime.now().subtract(const Duration(minutes: 30)),
    targetRoute: '/report',
  ),
];
