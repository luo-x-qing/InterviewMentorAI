import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/utils/helpers.dart';
import 'package:frontend_flutter/models/post.dart';
import 'package:frontend_flutter/services/post_service.dart';
import 'package:frontend_flutter/pages/post_detail_page.dart';
import 'package:frontend_flutter/pages/create_post_page.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

class CommunityPage extends StatefulWidget {
  const CommunityPage({super.key});

  @override
  State<CommunityPage> createState() => _CommunityPageState();
}

class _CommunityPageState extends State<CommunityPage> {
  static const _categories = ['全部', '面经分享', '技术讨论', '求职互助'];

  int _selectedCategory = 0;
  List<PostModel> _posts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadPosts();
  }

  Future<void> _loadPosts() async {
    final cat = _selectedCategory == 0 ? null : _categories[_selectedCategory];
    _posts = await PostService.getPosts(category: cat);
    if (mounted) setState(() => _loading = false);
  }

  void _onCategoryChanged(int index) {
    setState(() {
      _selectedCategory = index;
      _loading = true;
    });
    _loadPosts();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    await _loadPosts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('社区')),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CreatePostPage()),
          );
          if (result == true) _refresh();
        },
        backgroundColor: AppTheme.brand500,
        child: const Icon(Icons.edit, color: Colors.white),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
          : Column(
              children: [
                _buildCategoryTabs(),
                Expanded(child: _buildPostList()),
              ],
            ),
    );
  }

  Widget _buildCategoryTabs() {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
        itemCount: _categories.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final active = _selectedCategory == index;
          return GestureDetector(
            onTap: () => _onCategoryChanged(index),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 240),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: active ? AppTheme.gradientPrimary : null,
                color: active ? null : AppTheme.bgCard,
                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                border: active ? null : Border.all(color: AppTheme.borderLight),
              ),
              child: Text(_categories[index],
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
                      color: active ? Colors.white : AppTheme.textSecondary)),
            ),
          );
        },
      ),
    );
  }

  Widget _buildPostList() {
    if (_posts.isEmpty) {
      return EmptyStateWidget(
        icon: Icons.forum,
        title: '暂无帖子',
        subtitle: '该分类下还没有内容，去发布第一篇吧',
        action: FilledButton.icon(
          onPressed: () async {
            await Navigator.push(context,
                MaterialPageRoute(builder: (_) => const CreatePostPage()));
            _refresh();
          },
          icon: const Icon(Icons.edit, size: 16),
          label: const Text('发布帖子'),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
        itemCount: _posts.length,
        itemBuilder: (context, index) => _PostCard(post: _posts[index]),
      ),
    );
  }
}

/// 帖子卡片
class _PostCard extends StatelessWidget {
  final PostModel post;
  const _PostCard({required this.post});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: AppTheme.cardDecoration,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppTheme.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppTheme.radiusLg),
          onTap: () async {
            await Navigator.push(context,
                MaterialPageRoute(builder: (_) => PostDetailPage(postId: post.id)));
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 作者行
                Row(
                  children: [
                    Container(
                      width: 32, height: 32,
                      decoration: BoxDecoration(
                        gradient: AppTheme.gradientPrimary,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Center(
                        child: Text(post.authorName[0],
                            style: const TextStyle(color: Colors.white,
                                fontWeight: FontWeight.w600, fontSize: 14)),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(post.authorName,
                          style: const TextStyle(fontSize: 13,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.textPrimary)),
                    ),
                    Text(AppHelpers.relativeTime(post.createdAt),
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  ],
                ),
                const SizedBox(height: 10),
                // 标题
                Text(post.title,
                    style: const TextStyle(fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary),
                    maxLines: 2, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 6),
                // 内容预览
                Text(post.content.replaceAll(RegExp(r'[#*`\[\]\(\)\|]'), '').substring(0, post.content.length < 120 ? post.content.length : 120),
                    maxLines: 3, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, height: 1.4)),
                const SizedBox(height: 10),
                // 标签 + 操作栏
                Row(
                  children: [
                    ...post.tags.map((tag) => Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.brand50,
                          borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                        ),
                        child: Text(tag, style: const TextStyle(fontSize: 11,
                            color: AppTheme.brand500, fontWeight: FontWeight.w500)),
                      ),
                    )),
                    const Spacer(),
                    // 点赞
                    GestureDetector(
                      onTap: () async {
                        await PostService.toggleLike(post.id);
                      },
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(post.isLiked ? Icons.favorite : Icons.favorite_border,
                              size: 16, color: post.isLiked ? AppTheme.error : AppTheme.textMuted),
                          const SizedBox(width: 3),
                          Text('${post.likeCount}',
                              style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Icon(Icons.chat_bubble_outline, size: 16, color: AppTheme.textMuted),
                    const SizedBox(width: 3),
                    Text('${post.commentCount}',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                  ],
                ),
                // 关联报告（如有）
                if (post.linkedReportSummary != null) ...[
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.brand50,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.description, size: 16, color: AppTheme.brand500),
                        const SizedBox(width: 8),
                        Text('面试评分：${post.linkedReportSummary!['score']}分 ${post.linkedReportSummary!['grade']}',
                            style: const TextStyle(fontSize: 12, color: AppTheme.brand500)),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
