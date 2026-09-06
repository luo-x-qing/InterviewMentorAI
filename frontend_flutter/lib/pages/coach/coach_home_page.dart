import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/coach_service.dart';
import 'package:frontend_flutter/pages/coach/coach_session_page.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

/// 教练陪练主页：画像概览 + 推荐练习 + 开始陪练
class CoachHomePage extends StatefulWidget {
  const CoachHomePage({super.key});

  @override
  State<CoachHomePage> createState() => _CoachHomePageState();
}

class _CoachHomePageState extends State<CoachHomePage> {
  bool _loading = true;
  String? _error;

  List<String> _weaknesses = const [];
  List<String> _strengths = const [];
  Map<String, dynamic> _mastery = const {};
  List<CoachQuestion> _recommends = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final profile = await CoachService.getProfile();
      final recommends = await CoachService.recommend(limit: 3);
      if (!mounted) return;
      setState(() {
        _weaknesses = (profile['weaknesses'] as List<dynamic>? ?? [])
            .whereType<String>()
            .toList();
        _strengths = (profile['strengths'] as List<dynamic>? ?? [])
            .whereType<String>()
            .toList();
        _mastery = (profile['mastery'] as Map<String, dynamic>? ?? const {});
        _recommends = recommends;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _startSession() async {
    try {
      final handle = await CoachService.startSession(mode: 'TEXT', difficulty: 'MEDIUM');
      if (!mounted) return;
      final sessionId = handle['session_id'] as String;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CoachSessionPage(sessionId: sessionId),
        ),
      ).then((_) => _load());
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('开启陪练失败: $e'), backgroundColor: AppTheme.error),
      );
    }
  }

  void _practiceQuestion(CoachQuestion question) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CoachSessionPage(presetQuestion: question),
      ),
    ).then((_) => _load());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('陪练')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.brand500));
    }
    if (_error != null) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        child: Column(
          children: [
            EmptyStateWidget(
              icon: Icons.cloud_off,
              title: '加载失败',
              subtitle: _error,
              action: ElevatedButton.icon(
                onPressed: _load,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('重试'),
              ),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        children: [
          const SizedBox(height: 4),
          _buildHeroCard(),
          const SizedBox(height: 24),
          _buildSectionTitle('薄弱点画像', '根据历次评估归纳，重点攻克'),
          const SizedBox(height: 12),
          _buildProfileCard(),
          const SizedBox(height: 24),
          _buildSectionTitle('推荐练习', '基于弱点针对性选题'),
          const SizedBox(height: 12),
          if (_recommends.isEmpty) _buildNoRecommend(),
          ..._recommends.map((q) => _buildRecommendCard(q)),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildHeroCard() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.brand500,
        borderRadius: BorderRadius.circular(AppTheme.radiusLg),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('AI 陪练',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: Colors.white70)),
          const SizedBox(height: 8),
          const Text('模拟面试问答，即时点评',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600,
                  color: Colors.white, letterSpacing: -0.03)),
          const SizedBox(height: 6),
          const Text('文字作答即可获得逐题反馈与结课报告',
              style: TextStyle(fontSize: 14, color: Colors.white70, height: 1.5)),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _startSession,
              style: FilledButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: AppTheme.brand700,
              ),
              icon: const Icon(Icons.record_voice_over, size: 20),
              label: const Text('开始陪练'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title, String subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary)),
        const SizedBox(height: 2),
        Text(subtitle,
            style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
      ],
    );
  }

  Widget _buildProfileCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: _weaknesses.isEmpty && _strengths.isEmpty && _mastery.isEmpty
          ? const Text('暂无可画像数据，完成一次复盘或陪练后自动生成',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary))
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_mastery.isNotEmpty) ...[
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final e in _mastery.entries)
                        _buildMasteryChip(e.key, e.value),
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
                _buildTagRow('待加强', _weaknesses, AppTheme.warning),
                const SizedBox(height: 12),
                _buildTagRow('较扎实', _strengths, AppTheme.success),
              ],
            ),
    );
  }

  Widget _buildMasteryChip(String label, Object? value) {
    final v = (value as num?)?.toDouble() ?? 0;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppTheme.brand50,
        borderRadius: BorderRadius.circular(AppTheme.radiusMd),
        border: Border.all(color: AppTheme.brand100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(2),
                child: SizedBox(
                  width: 72,
                  height: 4,
                  child: LinearProgressIndicator(
                    value: v / 100,
                    backgroundColor: AppTheme.borderLight,
                    valueColor: AlwaysStoppedAnimation(
                        v < 60 ? AppTheme.warning : AppTheme.brand500),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Text('${v.toInt()}',
                  style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTagRow(String label, List<String> tags, Color color) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 56,
          child: Text(label,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: color)),
        ),
        Expanded(
          child: Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final t in tags)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                    border: Border.all(color: color.withValues(alpha: 0.25)),
                  ),
                  child: Text(t,
                      style: TextStyle(fontSize: 12, color: color)),
                ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildNoRecommend() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppTheme.radiusMd),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: const Text('暂无推荐：先完成一次复盘或一轮陪练，即可按弱点生成练习',
          style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
    );
  }

  Widget _buildRecommendCard(CoachQuestion q) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: AppTheme.cardDecoration,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppTheme.radiusLg),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppTheme.radiusLg),
          onTap: () => _practiceQuestion(q),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    color: AppTheme.brand50,
                    borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                  ),
                  child: const Icon(Icons.quiz_outlined, color: AppTheme.brand500, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(q.title,
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 4),
                      Text(q.question,
                          maxLines: 2, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13,
                              color: AppTheme.textSecondary)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}