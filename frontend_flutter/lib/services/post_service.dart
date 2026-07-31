import 'package:frontend_flutter/models/post.dart';
import 'package:frontend_flutter/data/mock_posts.dart';

/// 帖子服务 —— 当前使用 mock 数据，预留 API 切换接口
class PostService {
  static List<PostModel>? _cachedPosts;

  /// 获取帖子列表（支持分类筛选）
  static Future<List<PostModel>> getPosts({String? category}) async {
    _cachedPosts ??= List.from(mockPosts);
    if (category == null || category == '全部') return _cachedPosts!;
    return _cachedPosts!.where((p) {
      // 按标签匹配分类
      final catLower = category;
      return p.tags.any((t) => t == catLower) || p.tags.contains(category);
    }).toList();
  }

  /// 获取帖子详情（含评论）
  static Future<PostModel?> getPostDetail(String id) async {
    _cachedPosts ??= List.from(mockPosts);
    try {
      return _cachedPosts!.firstWhere((p) => p.id == id);
    } catch (_) {
      return null;
    }
  }

  /// 切换点赞状态
  static Future<int> toggleLike(String postId) async {
    _cachedPosts ??= List.from(mockPosts);
    try {
      final post = _cachedPosts!.firstWhere((p) => p.id == postId);
      post.isLiked = !post.isLiked;
      post.likeCount += post.isLiked ? 1 : -1;
      return post.likeCount;
    } catch (_) {
      return 0;
    }
  }

  /// 添加评论
  static Future<CommentModel?> addComment(String postId, String author, String content) async {
    _cachedPosts ??= List.from(mockPosts);
    try {
      final post = _cachedPosts!.firstWhere((p) => p.id == postId);
      final comment = CommentModel(
        id: 'c${DateTime.now().millisecondsSinceEpoch}',
        postId: postId, authorName: author, content: content,
        createdAt: DateTime.now(),
      );
      post.comments.add(comment);
      post.commentCount = post.comments.length;
      return comment;
    } catch (_) {
      return null;
    }
  }

  /// 创建新帖子
  static Future<PostModel> createPost(PostModel post) async {
    _cachedPosts ??= List.from(mockPosts);
    _cachedPosts!.insert(0, post);
    return post;
  }
}
