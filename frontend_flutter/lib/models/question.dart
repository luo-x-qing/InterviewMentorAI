/// 面试题目数据模型
class InterviewQuestion {
  final String id;
  final String category;      // HTML/CSS, JavaScript, React/Vue, 算法, 系统设计, 行为问题
  final String difficulty;    // 初级, 中级, 高级
  final String title;         // 题目
  final String answer;        // 参考答案（Markdown）
  final String intent;        // 出题意图
  final List<String> tags;    // 标签
  bool isFavorite;

  InterviewQuestion({
    required this.id,
    required this.category,
    required this.difficulty,
    required this.title,
    required this.answer,
    required this.intent,
    required this.tags,
    this.isFavorite = false,
  });

  /// 难度对应的颜色（使用 AppTheme 色系）
  static const difficultyColors = {
    '初级': 0xFF22C55E,   // success
    '中级': 0xFFD97706,   // warning
    '高级': 0xFFEF4444,   // error
  };
}
