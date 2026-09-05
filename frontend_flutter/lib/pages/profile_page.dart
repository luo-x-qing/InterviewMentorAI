import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/auth_service.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/pages/interview_history_page.dart';
import 'package:frontend_flutter/pages/settings_page.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  Map<String, dynamic>? _userInfo;
  bool _loading = true;

  // 模拟统计数据
  final int _totalInterviews = 6;
  final double _averageScore = 80.5;
  final int _maxScore = 92;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final resp = await ApiService.getUserProfile();
      if (resp['code'] == 200 && mounted) {
        setState(() => _userInfo = resp['data'] as Map<String, dynamic>?);
      }
    } catch (_) {
      // 加载失败使用默认值
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _logout() async {
    await AuthService.logout();
    if (mounted) {
      Navigator.of(context).pushNamedAndRemoveUntil('/login', (_) => false);
    }
  }

  String get _displayName =>
      _userInfo?['nickname'] as String? ??
      _userInfo?['username'] as String? ??
      '用户';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('我')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
          : ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                _buildUserCard(),
                const SizedBox(height: 20),
                _buildStatsRow(),
                const SizedBox(height: 24),
                _menuItem(Icons.history, '面试记录', () {
                  Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const InterviewHistoryPage()));
                }),
                _menuItem(Icons.settings_outlined, '设置', () {
                  Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const SettingsPage()));
                }),
                const SizedBox(height: 32),
                _buildLogoutButton(),
              ],
            ),
    );
  }

  Widget _buildUserCard() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.cardDecoration,
      child: Row(
        children: [
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppTheme.gradientStart, AppTheme.gradientEnd]),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.person, size: 32, color: Colors.white),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_displayName,
                    style: const TextStyle(fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary)),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.successBg,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                  ),
                  child: const Text('个人用户',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500,
                          color: AppTheme.success)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// 面试统计概览卡片（总次数 / 平均分 / 最高分）
  Widget _buildStatsRow() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 8),
      decoration: AppTheme.cardDecoration,
      child: Row(
        children: [
          _statItem(Icons.mic, _totalInterviews.toString(), '总面试次数'),
          Container(width: 1, height: 36, color: AppTheme.borderLight),
          _statItem(Icons.trending_up, _averageScore.toStringAsFixed(1), '平均得分'),
          Container(width: 1, height: 36, color: AppTheme.borderLight),
          _statItem(Icons.emoji_events, _maxScore.toString(), '最高得分'),
        ],
      ),
    );
  }

  Widget _statItem(IconData icon, String value, String label) {
    return Expanded(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 22, color: AppTheme.brand500),
          const SizedBox(height: 6),
          Text(value,
              style: const TextStyle(fontSize: 22,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.brand500)),
          const SizedBox(height: 2),
          Text(label,
              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
        ],
      ),
    );
  }

  Widget _menuItem(IconData icon, String label, VoidCallback onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 1),
      child: ListTile(
        leading: Icon(icon, color: AppTheme.textSecondary),
        title: Text(label,
            style: const TextStyle(fontSize: 15, color: AppTheme.textPrimary)),
        trailing: const Icon(Icons.chevron_right, color: AppTheme.textMuted),
        onTap: onTap,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTheme.radiusSm),
        ),
      ),
    );
  }

  Widget _buildLogoutButton() {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: _logout,
        icon: const Icon(Icons.logout, size: 18),
        label: const Text('退出登录'),
        style: OutlinedButton.styleFrom(
          foregroundColor: AppTheme.error,
          side: BorderSide(color: AppTheme.error.withValues(alpha: 0.3)),
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          ),
        ),
      ),
    );
  }
}
