/// 社区帖子模型
class PostModel {
  final String id;
  final String authorName;
  final String title;
  final String content;        // Markdown
  final List<String> tags;
  int likeCount;
  int commentCount;
  bool isLiked;
  final DateTime createdAt;
  final String? linkedReportId;
  final Map<String, dynamic>? linkedReportSummary; // 关联报告的简要摘要
  final List<CommentModel> comments;

  PostModel({
    required this.id,
    required this.authorName,
    required this.title,
    required this.content,
    required this.tags,
    this.likeCount = 0,
    this.commentCount = 0,
    this.isLiked = false,
    required this.createdAt,
    this.linkedReportId,
    this.linkedReportSummary,
    this.comments = const [],
  });
}

/// 评论模型
class CommentModel {
  final String id;
  final String postId;
  final String authorName;
  final String content;
  final DateTime createdAt;

  CommentModel({
    required this.id,
    required this.postId,
    required this.authorName,
    required this.content,
    required this.createdAt,
  });
}
