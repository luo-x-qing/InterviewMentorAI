/// 全局工具函数 —— 评分等级、时间格式化、相对时间
class AppHelpers {
  AppHelpers._();

  /// 将数值分数映射为中文评级标签
  static String gradeLabel(int score) {
    if (score >= 90) return '卓越';
    if (score >= 80) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 60) return '一般';
    return '待提高';
  }

  /// 将秒数格式化为 MM:SS 显示字符串
  static String formatTime(int seconds) {
    final m = (seconds ~/ 60).toString().padLeft(2, '0');
    final s = (seconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  /// 将 DateTime 转为相对时间描述（如 "3分钟前"、"昨天"）
  static String relativeTime(DateTime dateTime) {
    final diff = DateTime.now().difference(dateTime);
    if (diff.inSeconds < 60) return '刚刚';
    if (diff.inMinutes < 60) return '${diff.inMinutes}分钟前';
    if (diff.inHours < 24) return '${diff.inHours}小时前';
    if (diff.inDays < 7) return '${diff.inDays}天前';
    return '${dateTime.month}/${dateTime.day}';
  }
}
