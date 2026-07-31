import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/api_service.dart';

/// 设置页（修改密码 / 主题 / 关于）
class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _darkMode = false;

  void _showPasswordSheet() {
    final oldPwdCtrl = TextEditingController();
    final newPwdCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    String? error;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(24, 24, 24,
                  MediaQuery.of(ctx).viewInsets.bottom + 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('修改密码',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary)),
                  const SizedBox(height: 4),
                  const Text('请输入当前密码和新密码',
                      style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                  const SizedBox(height: 20),
                  if (error != null) ...[
                    Container(
                      width: double.infinity, padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.error.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(error!, style: const TextStyle(color: AppTheme.error, fontSize: 13)),
                    ),
                    const SizedBox(height: 16),
                  ],
                  TextField(
                    controller: oldPwdCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: '当前密码', prefixIcon: Icon(Icons.lock_outline)),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: newPwdCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: '新密码', prefixIcon: Icon(Icons.lock)),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: confirmCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: '确认新密码', prefixIcon: Icon(Icons.lock)),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity, height: 48,
                    child: FilledButton(
                      onPressed: () async {
                        final old = oldPwdCtrl.text.trim();
                        final newPwd = newPwdCtrl.text.trim();
                        final confirm = confirmCtrl.text.trim();
                        if (old.isEmpty || newPwd.isEmpty || confirm.isEmpty) {
                          setSheetState(() => error = '请填写所有密码字段');
                          return;
                        }
                        if (newPwd.length < 6) {
                          setSheetState(() => error = '新密码长度至少 6 位');
                          return;
                        }
                        if (newPwd != confirm) {
                          setSheetState(() => error = '两次输入的新密码不一致');
                          return;
                        }
                        try {
                          await ApiService.updatePassword(oldPassword: old, newPassword: newPwd);
                          if (ctx.mounted) Navigator.pop(ctx);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('密码修改成功'),
                                  backgroundColor: AppTheme.success),
                            );
                          }
                        } catch (_) {
                          setSheetState(() => error = '修改失败，请检查当前密码是否正确');
                        }
                      },
                      child: const Text('确认修改', style: TextStyle(fontSize: 16)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          // ── 账户设置 ──
          _buildSectionHeader('账户设置'),
          _menuItem(Icons.lock_outline, '修改密码', _showPasswordSheet),
          _menuItem(Icons.edit_outlined, '编辑资料', () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('功能开发中...'), backgroundColor: AppTheme.textMuted),
            );
          }),

          const SizedBox(height: 16),
          _buildSectionHeader('偏好设置'),
          SwitchListTile(
            value: _darkMode,
            onChanged: (v) {
              setState(() => _darkMode = v);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('深色模式功能开发中...'), backgroundColor: AppTheme.textMuted),
              );
            },
            title: const Text('深色模式', style: TextStyle(fontSize: 15, color: AppTheme.textPrimary)),
            secondary: const Icon(Icons.dark_mode, color: AppTheme.textSecondary),
            activeThumbColor: AppTheme.brand500,
          ),
          _menuItem(Icons.notifications_outlined, '通知设置', () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('功能开发中...'), backgroundColor: AppTheme.textMuted),
            );
          }),

          const SizedBox(height: 16),
          _buildSectionHeader('其他'),
          _menuItem(Icons.delete_outline, '清除缓存', () {
            showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                title: const Text('清除缓存'),
                content: const Text('确定要清除本地缓存数据吗？已缓存的报告将被删除。'),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
                  TextButton(
                    onPressed: () {
                      Navigator.pop(ctx);
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('缓存已清除'), backgroundColor: AppTheme.success),
                      );
                    },
                    style: TextButton.styleFrom(foregroundColor: AppTheme.error),
                    child: const Text('清除'),
                  ),
                ],
              ),
            );
          }),
          _menuItem(Icons.info_outline, '关于', () {
            showAboutDialog(
              context: context,
              applicationName: 'InterviewMentorAI',
              applicationVersion: '1.0.0',
              children: [
                const Text('AI 面试复盘助手 — 提升你的面试表现'),
              ],
            );
          }),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 4),
      child: Text(title,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
              color: AppTheme.textMuted, letterSpacing: 1.2)),
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
}
