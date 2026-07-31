import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/utils/helpers.dart';
import 'package:frontend_flutter/models/post.dart';
import 'package:frontend_flutter/services/post_service.dart';

/// 帖子详情页（含评论 + 点赞）
class PostDetailPage extends StatefulWidget {
  final String postId;
  const PostDetailPage({super.key, required this.postId});

  @override
  State<PostDetailPage> createState() => _PostDetailPageState();
}

class _PostDetailPageState extends State<PostDetailPage> {
  PostModel? _post;
  bool _loading = true;
  final _commentCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadPost();
  }

  @override
  void dispose() {
    _commentCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadPost() async {
    _post = await PostService.getPostDetail(widget.postId);
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _toggleLike() async {
    if (_post == null) return;
    final count = await PostService.toggleLike(widget.postId);
    setState(() {
      _post!.isLiked = !_post!.isLiked;
      _post!.likeCount = count;
    });
  }

  Future<void> _addComment() async {
    final content = _commentCtrl.text.trim();
    if (content.isEmpty) return;
    await PostService.addComment(widget.postId, '我', content);
    _commentCtrl.clear();
    await _loadPost();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('帖子详情')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
          : _post == null
              ? const Center(child: Text('帖子不存在'))
              : Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_post!.title,
                                style: const TextStyle(fontSize: 20,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textPrimary)),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Text(_post!.authorName,
                                    style: const TextStyle(fontSize: 13,
                                        color: AppTheme.textSecondary)),
                                const SizedBox(width: 12),
                                Text(AppHelpers.relativeTime(_post!.createdAt),
                                    style: const TextStyle(fontSize: 12,
                                        color: AppTheme.textMuted)),
                              ],
                            ),
                            const SizedBox(height: 16),
                            Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: AppTheme.bgPage,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: AppTheme.borderLight),
                              ),
                              child: MarkdownBody(data: _post!.content,
                                  styleSheet: MarkdownStyleSheet(
                                    p: const TextStyle(fontSize: 14,
                                        color: AppTheme.textSecondary, height: 1.7),
                                  )),
                            ),
                            if (_post!.linkedReportSummary != null) ...[
                              const SizedBox(height: 16),
                              Container(
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: AppTheme.brand50,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Row(
                                  children: [
                                    const Icon(Icons.description, color: AppTheme.brand500),
                                    const SizedBox(width: 10),
                                    Text('关联面试：${_post!.linkedReportSummary!['score']}分 ${_post!.linkedReportSummary!['grade']}',
                                        style: const TextStyle(color: AppTheme.brand500)),
                                  ],
                                ),
                              ),
                            ],
                            const SizedBox(height: 20),
                            // 评论标题
                            Text('评论 (${_post!.commentCount})',
                                style: const TextStyle(fontSize: 15,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textPrimary)),
                            const SizedBox(height: 12),
                            ..._post!.comments.map((c) => _commentTile(c)),
                          ],
                        ),
                      ),
                    ),
                    // 底部操作栏
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.bgCard,
                        border: Border(top: BorderSide(color: AppTheme.borderLight)),
                      ),
                      child: SafeArea(
                        child: Row(
                          children: [
                            GestureDetector(
                              onTap: _toggleLike,
                              child: Row(
                                children: [
                                  Icon(_post!.isLiked ? Icons.favorite : Icons.favorite_border,
                                      color: _post!.isLiked ? AppTheme.error : AppTheme.textSecondary),
                                  const SizedBox(width: 4),
                                  Text('${_post!.likeCount}',
                                      style: const TextStyle(color: AppTheme.textSecondary)),
                                ],
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: TextField(
                                controller: _commentCtrl,
                                decoration: InputDecoration(
                                  hintText: '写评论...',
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                                    borderSide: const BorderSide(color: AppTheme.borderLight),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            IconButton(
                              onPressed: _addComment,
                              icon: const Icon(Icons.send, color: AppTheme.brand500),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _commentTile(CommentModel comment) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              color: AppTheme.brand100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Text(comment.authorName[0],
                  style: const TextStyle(color: AppTheme.brand500,
                      fontWeight: FontWeight.w600, fontSize: 13)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(comment.authorName,
                        style: const TextStyle(fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: AppTheme.textPrimary)),
                    const SizedBox(width: 8),
                    Text(AppHelpers.relativeTime(comment.createdAt),
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(comment.content,
                    style: const TextStyle(fontSize: 13,
                        color: AppTheme.textSecondary, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
