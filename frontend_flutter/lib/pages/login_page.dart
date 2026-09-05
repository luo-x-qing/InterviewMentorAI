import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/auth_service.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage>
    with SingleTickerProviderStateMixin {
  bool _isRegister = false;

  late final TabController _tabCtrl;

  final _phoneCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _nicknameCtrl = TextEditingController();

  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
    _tabCtrl.addListener(() {
      setState(() => _isRegister = _tabCtrl.index == 1);
    });
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _phoneCtrl.dispose();
    _passwordCtrl.dispose();
    _nicknameCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final phone = _phoneCtrl.text.trim();
    final password = _passwordCtrl.text.trim();
    if (phone.isEmpty || password.isEmpty) {
      return _setError('手机号和密码不能为空');
    }
    if (password.length < 6) {
      return _setError('密码长度至少 6 位');
    }
    _setLoading(true);
    try {
      if (_isRegister) {
        await AuthService.register(
          phone: phone,
          password: password,
          nickname: _nicknameCtrl.text.trim(),
        );
      } else {
        await AuthService.login(phone: phone, password: password);
      }
      if (mounted) {
        Navigator.of(context).pushNamedAndRemoveUntil('/', (route) => false);
      }
    } catch (e) {
      _setError(_isRegister
          ? '注册失败，请检查输入或更换手机号'
          : '登录失败，请检查手机号和密码');
    }
  }

  void _setError(String msg) {
    setState(() { _error = msg; _loading = false; });
  }

  void _setLoading(bool v) {
    setState(() { _loading = v; _error = null; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildLogo(),
                  const SizedBox(height: 32),
                  _buildCard(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Column(
      children: [
        Container(
          width: 72, height: 72,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.gradientStart, AppTheme.gradientEnd]),
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [
              BoxShadow(color: Color(0x334F46E5), blurRadius: 16, offset: Offset(0, 4)),
            ],
          ),
          child: const Icon(Icons.psychology, size: 36, color: Colors.white),
        ),
        const SizedBox(height: 16),
        const Text('InterviewMentorAI',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary)),
        const SizedBox(height: 4),
        const Text('AI 面试复盘助手',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
      ],
    );
  }

  Widget _buildCard() {
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: AppTheme.cardDecoration,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            decoration: BoxDecoration(
              color: AppTheme.bgPage,
              borderRadius: BorderRadius.circular(12),
            ),
            child: TabBar(
              controller: _tabCtrl,
              indicator: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.gradientStart, AppTheme.gradientEnd]),
                borderRadius: BorderRadius.circular(10),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              labelColor: Colors.white,
              unselectedLabelColor: AppTheme.textSecondary,
              tabs: const [
                Tab(text: '登录'), Tab(text: '注册'),
              ],
            ),
          ),
          const SizedBox(height: 24),

          if (_error != null) ...[
            Container(
              width: double.infinity, padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.error.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_error!,
                  style: const TextStyle(color: AppTheme.error, fontSize: 13)),
            ),
            const SizedBox(height: 16),
          ],

          TextField(
            controller: _phoneCtrl,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: '手机号', prefixIcon: Icon(Icons.phone_outlined),
              border: OutlineInputBorder(),
            ),
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: 14),

          TextField(
            controller: _passwordCtrl,
            decoration: const InputDecoration(
              labelText: '密码', prefixIcon: Icon(Icons.lock_outline),
              border: OutlineInputBorder(),
            ),
            obscureText: true,
            textInputAction: _isRegister ? TextInputAction.next : TextInputAction.done,
            onSubmitted: _isRegister ? null : (_) => _submit(),
          ),
          const SizedBox(height: 14),

          if (_isRegister) ...[
            TextField(
              controller: _nicknameCtrl,
              decoration: const InputDecoration(
                labelText: '昵称（选填）', prefixIcon: Icon(Icons.badge_outlined),
                border: OutlineInputBorder(),
              ),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _submit(),
            ),
            const SizedBox(height: 14),
          ],

          SizedBox(
            width: double.infinity, height: 48,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.gradientStart, AppTheme.gradientEnd]),
                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                boxShadow: const [
                  BoxShadow(color: Color(0x334F46E5), blurRadius: 12, offset: Offset(0, 4)),
                ],
              ),
              child: FilledButton(
                onPressed: _loading ? null : _submit,
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.transparent, shadowColor: Colors.transparent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull)),
                ),
                child: _loading
                    ? const SizedBox(width: 22, height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(_isRegister ? '注 册' : '登 录',
                        style: const TextStyle(fontSize: 16)),
              ),
            ),
          ),
          const SizedBox(height: 14),

          GestureDetector(
            onTap: () {
              setState(() {
                _error = null;
                _tabCtrl.index = _isRegister ? 0 : 1;
              });
            },
            child: Text(
              _isRegister ? '已有账号？去登录' : '还没有账号？去注册',
              style: const TextStyle(
                fontSize: 12, fontWeight: FontWeight.w500,
                color: AppTheme.brand500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
