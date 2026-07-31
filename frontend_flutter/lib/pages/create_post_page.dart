import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/models/post.dart';
import 'package:frontend_flutter/services/post_service.dart';

/// 发布帖子页
class CreatePostPage extends StatefulWidget {
  const CreatePostPage({super.key});

  @override
  State<CreatePostPage> createState() => _CreatePostPageState();
}

class _CreatePostPageState extends State<CreatePostPage> {
  final _titleCtrl = TextEditingController();
  final _contentCtrl = TextEditingController();
  final _tagsCtrl = TextEditingController();
  String _category = '面经分享';
  bool _submitting = false;

  static const _categories = ['面经分享', '技术讨论', '求职互助'];

  @override
  void dispose() {
    _titleCtrl.dispose();
    _contentCtrl.dispose();
    _tagsCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final title = _titleCtrl.text.trim();
    final content = _contentCtrl.text.trim();
    final tagsStr = _tagsCtrl.text.trim();

    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入标题'), backgroundColor: AppTheme.error),
      );
      return;
    }
    if (content.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入内容'), backgroundColor: AppTheme.error),
      );
      return;
    }

    final tags = [_category];
    if (tagsStr.isNotEmpty) {
      tags.addAll(tagsStr.split(',').map((t) => t.trim()).where((t) => t.isNotEmpty));
    }

    setState(() => _submitting = true);
    final post = PostModel(
      id: 'p${DateTime.now().millisecondsSinceEpoch}',
      authorName: '我',
      title: title,
      content: content,
      tags: tags,
      createdAt: DateTime.now(),
    );

    await PostService.createPost(post);
    if (mounted) Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        title: const Text('发布帖子'),
        actions: [
          TextButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.brand500))
                : const Text('发布', style: TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _titleCtrl,
              decoration: const InputDecoration(
                hintText: '输入帖子标题...',
                border: OutlineInputBorder(),
              ),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 14),
            // 分类选择
            DropdownButtonFormField<String>(
              initialValue: _category,
              decoration: const InputDecoration(labelText: '分类', border: OutlineInputBorder()),
              items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
              onChanged: (v) => setState(() => _category = v!),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _contentCtrl,
              maxLines: 10,
              decoration: const InputDecoration(
                hintText: '分享你的面试经验、技术心得...',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _tagsCtrl,
              decoration: const InputDecoration(
                hintText: '标签（逗号分隔，如：React, 面经）',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity, height: 48,
              child: FilledButton(
                onPressed: _submitting ? null : _submit,
                child: const Text('发布', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
