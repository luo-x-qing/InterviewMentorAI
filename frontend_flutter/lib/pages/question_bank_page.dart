import 'dart:async';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/models/question.dart';
import 'package:frontend_flutter/data/mock_questions.dart';
import 'package:frontend_flutter/services/favorite_service.dart';
import 'package:frontend_flutter/pages/record_page.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

class QuestionBankPage extends StatefulWidget {
  const QuestionBankPage({super.key});

  @override
  State<QuestionBankPage> createState() => _QuestionBankPageState();
}

class _QuestionBankPageState extends State<QuestionBankPage> {
  // 分类列表
  static const _categories = [
    '全部', 'HTML/CSS', 'JavaScript', 'React/Vue', '算法', '系统设计', '行为问题'
  ];

  int _selectedCategory = 0;       // 当前分类索引
  String _searchQuery = '';        // 搜索关键词
  Timer? _debounceTimer;           // 搜索防抖
  bool _loading = true;

  // 难度筛选 (null = 全部)
  String? _selectedDifficulty;

  // 收藏 ID 集合
  Set<String> _favoriteIds = {};

  // 过滤后的题目列表
  List<InterviewQuestion> _filteredQuestions = [];

  @override
  void initState() {
    super.initState();
    _loadFavorites();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadFavorites() async {
    _favoriteIds = await FavoriteService.getFavorites();
    _applyFilters();
    setState(() => _loading = false);
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      setState(() {
        _searchQuery = value.trim();
        _applyFilters();
      });
    });
  }

  void _onCategoryChanged(int index) {
    setState(() {
      _selectedCategory = index;
      _applyFilters();
    });
  }

  void _onDifficultyChanged(String? difficulty) {
    setState(() {
      _selectedDifficulty = _selectedDifficulty == difficulty ? null : difficulty;
      _applyFilters();
    });
  }

  Future<void> _toggleFavorite(String questionId) async {
    final isFav = await FavoriteService.toggle(questionId);
    setState(() {
      if (isFav) {
        _favoriteIds.add(questionId);
      } else {
        _favoriteIds.remove(questionId);
      }
    });
  }

  void _applyFilters() {
    var list = List<InterviewQuestion>.from(mockQuestions);

    // 分类筛选
    if (_selectedCategory > 0) {
      final cat = _categories[_selectedCategory];
      list = list.where((q) => q.category == cat).toList();
    }

    // 难度筛选
    if (_selectedDifficulty != null) {
      list = list.where((q) => q.difficulty == _selectedDifficulty).toList();
    }

    // 搜索
    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      list = list.where((q) =>
          q.title.toLowerCase().contains(query) ||
          q.tags.any((t) => t.toLowerCase().contains(query)) ||
          q.answer.toLowerCase().contains(query)
      ).toList();
    }

    // 同步收藏状态
    for (final q in list) {
      q.isFavorite = _favoriteIds.contains(q.id);
    }

    _filteredQuestions = list;
  }

  void _startMockInterview(InterviewQuestion question) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => RecordPage(
          questionTitle: question.title,
          questionText: question.title,
          onComplete: (reportData) {
            // 面试完成，可选处理
          },
        ),
      ),
    );
  }

  Color _difficultyColor(String difficulty) {
    switch (difficulty) {
      case '初级': return AppTheme.success;
      case '中级': return AppTheme.warning;
      case '高级': return AppTheme.error;
      default: return AppTheme.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('题库')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
          : Column(
              children: [
                _buildSearchBar(),
                _buildCategoryTabs(),
                _buildDifficultyFilter(),
                Expanded(child: _buildQuestionList()),
              ],
            ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 4),
      child: TextField(
        onChanged: _onSearchChanged,
        decoration: InputDecoration(
          hintText: '搜索题目、标签...',
          prefixIcon: const Icon(Icons.search, color: AppTheme.textMuted, size: 22),
          suffixIcon: _searchQuery.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear, size: 18),
                  onPressed: () {
                    setState(() {
                      _searchQuery = '';
                      _applyFilters();
                    });
                  },
                )
              : null,
          filled: true,
          fillColor: AppTheme.bgCard,
          contentPadding: const EdgeInsets.symmetric(vertical: 10),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            borderSide: const BorderSide(color: AppTheme.borderLight),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            borderSide: const BorderSide(color: AppTheme.borderLight),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            borderSide: const BorderSide(color: AppTheme.brand500, width: 1.5),
          ),
        ),
      ),
    );
  }

  /// 水平滚动分类 Tab（复用 home_page 胶囊 Tab 模式）
  Widget _buildCategoryTabs() {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
        itemCount: _categories.length,
        separatorBuilder: (context, idx) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final active = _selectedCategory == index;
          return GestureDetector(
            onTap: () => _onCategoryChanged(index),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 240),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: active ? AppTheme.brand500 : AppTheme.bgCard,
                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                border: active ? null : Border.all(color: AppTheme.borderLight),
              ),
              child: Text(
                _categories[index],
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: active ? Colors.white : AppTheme.textSecondary,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  /// 难度筛选 chips
  Widget _buildDifficultyFilter() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
      child: Row(
        children: [
          const Text('难度：', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          const SizedBox(width: 8),
          ...['初级', '中级', '高级'].map((d) {
            final selected = _selectedDifficulty == d;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: GestureDetector(
                onTap: () => _onDifficultyChanged(d),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                  decoration: BoxDecoration(
                    color: selected ? _difficultyColor(d) : AppTheme.bgCard,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                    border: Border.all(
                      color: selected ? _difficultyColor(d) : AppTheme.borderLight,
                    ),
                  ),
                  child: Text(d,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: selected ? Colors.white : AppTheme.textSecondary,
                    ),
                  ),
                ),
              ),
            );
          }),
          const Spacer(),
          Text('${_filteredQuestions.length} 题',
              style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
        ],
      ),
    );
  }

  Widget _buildQuestionList() {
    if (_filteredQuestions.isEmpty) {
      return EmptyStateWidget(
        icon: Icons.search_off,
        title: '未找到匹配的题目',
        subtitle: _searchQuery.isNotEmpty
            ? '没有与 "$_searchQuery" 相关的题目，请尝试其他关键词'
            : '该分类下暂无题目',
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      itemCount: _filteredQuestions.length,
      itemBuilder: (context, index) {
        return _QuestionCard(
          question: _filteredQuestions[index],
          onFavorite: () => _toggleFavorite(_filteredQuestions[index].id),
          onStartInterview: () => _startMockInterview(_filteredQuestions[index]),
        );
      },
    );
  }
}

/// 单张题目卡片
class _QuestionCard extends StatefulWidget {
  final InterviewQuestion question;
  final VoidCallback onFavorite;
  final VoidCallback onStartInterview;

  const _QuestionCard({
    required this.question,
    required this.onFavorite,
    required this.onStartInterview,
  });

  @override
  State<_QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<_QuestionCard> {
  bool _expanded = false;

  Color _diffColor(String d) {
    switch (d) {
      case '初级': return AppTheme.success;
      case '中级': return AppTheme.warning;
      case '高级': return AppTheme.error;
      default: return AppTheme.textMuted;
    }
  }

  Color _diffBg(String d) {
    switch (d) {
      case '初级': return AppTheme.successBg;
      case '中级': return AppTheme.warningBg;
      case '高级': return AppTheme.error.withValues(alpha: 0.15);
      default: return AppTheme.bgPage;
    }
  }

  @override
  Widget build(BuildContext context) {
    final q = widget.question;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: AppTheme.cardDecoration,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppTheme.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppTheme.radiusLg),
          onTap: () => setState(() => _expanded = !_expanded),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 第一行：分类标签 + 难度标签
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.brand50,
                        borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                      ),
                      child: Text(q.category,
                          style: const TextStyle(fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.brand500)),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                      decoration: BoxDecoration(
                        color: _diffBg(q.difficulty),
                        borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                      ),
                      child: Text(q.difficulty,
                          style: TextStyle(fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: _diffColor(q.difficulty))),
                    ),
                    const Spacer(),
                    GestureDetector(
                      onTap: widget.onFavorite,
                      child: Icon(
                        q.isFavorite ? Icons.favorite : Icons.favorite_border,
                        size: 20,
                        color: q.isFavorite ? AppTheme.error : AppTheme.textMuted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // 标题
                Text(q.title,
                    style: const TextStyle(fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary)),
                const SizedBox(height: 8),

                // 标签行
                Wrap(
                  spacing: 6, runSpacing: 4,
                  children: q.tags.map((tag) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.bgPage,
                      borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                    ),
                    child: Text(tag,
                        style: const TextStyle(fontSize: 11,
                            color: AppTheme.textSecondary)),
                  )).toList(),
                ),

                // 展开区
                AnimatedCrossFade(
                  firstChild: const SizedBox.shrink(),
                  secondChild: _buildExpandedContent(q),
                  crossFadeState: _expanded
                      ? CrossFadeState.showSecond
                      : CrossFadeState.showFirst,
                  duration: const Duration(milliseconds: 280),
                ),

                // 展开按钮
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton.icon(
                      onPressed: () => setState(() => _expanded = !_expanded),
                      icon: Icon(
                        _expanded ? Icons.expand_less : Icons.expand_more,
                        size: 18, color: AppTheme.brand500,
                      ),
                      label: Text(
                        _expanded ? '收起' : '查看详情',
                        style: const TextStyle(fontSize: 13, color: AppTheme.brand500),
                      ),
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                    ),
                    SizedBox(
                      height: 32,
                      child: FilledButton.icon(
                        onPressed: widget.onStartInterview,
                        icon: const Icon(Icons.mic, size: 16),
                        label: const Text('模拟面试', style: TextStyle(fontSize: 12)),
                        style: FilledButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildExpandedContent(InterviewQuestion q) {
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 参考答案
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppTheme.bgPage,
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 6, height: 6,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppTheme.brand500,
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text('参考答案',
                        style: TextStyle(fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary)),
                  ],
                ),
                const SizedBox(height: 10),
                Text(q.answer,
                    style: const TextStyle(fontSize: 13,
                        color: AppTheme.textSecondary, height: 1.7)),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // 出题意图
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppTheme.warningBg.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              border: Border.all(color: AppTheme.warningBg),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 6, height: 6,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppTheme.warning,
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text('出题意图',
                        style: TextStyle(fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary)),
                  ],
                ),
                const SizedBox(height: 10),
                Text(q.intent,
                    style: const TextStyle(fontSize: 13,
                        color: AppTheme.textSecondary, height: 1.7)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
