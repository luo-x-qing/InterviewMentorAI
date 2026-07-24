import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// 邀请码输入页面
///
/// 候选人通过 HR 提供的 6 位邀请码加入面试会话。
/// 输入邀请码 → 验证有效性 → 展示会话信息 → 进入录音。
class InviteCodePage extends StatefulWidget {
  const InviteCodePage({super.key});

  @override
  State<InviteCodePage> createState() => _InviteCodePageState();
}

class _InviteCodePageState extends State<InviteCodePage> {
  final _codeCtrl = TextEditingController();
  final Dio _dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: const Duration(seconds: 10),
  ));

  bool _checking = false;
  String? _error;
  Map<String, dynamic>? _session;

  Future<void> _checkCode() async {
    final code = _codeCtrl.text.trim().toUpperCase();
    if (code.isEmpty) {
      setState(() => _error = '请输入邀请码');
      return;
    }

    setState(() { _checking = true; _error = null; _session = null; });

    try {
      // 先检查是否有效
      final validResp = await _dio.get('${Constants.sessionCheckApi}/$code/valid');
      if (validResp.data['code'] == 200 && validResp.data['data'] == true) {
        // 获取会话详情
        final detailResp = await _dio.get('${Constants.sessionDetailApi}/$code');
        if (detailResp.data['code'] == 200) {
          setState(() => _session = detailResp.data['data'] as Map<String, dynamic>?);
        }
      } else {
        setState(() => _error = '邀请码无效或已过期');
      }
    } catch (e) {
      setState(() => _error = '网络错误：$e');
    } finally {
      setState(() => _checking = false);
    }
  }

  @override
  void dispose() {
    _codeCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('输入邀请码')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 48),
            Icon(Icons.link, size: 64, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 16),
            const Text('请输入 HR 提供的邀请码',
                style: TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 24),

            // 邀请码输入
            TextField(
              controller: _codeCtrl,
              decoration: const InputDecoration(
                labelText: '邀请码（6位大写字母）',
                hintText: '例如：ABC123',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.vpn_key_outlined),
              ),
              textCapitalization: TextCapitalization.characters,
              maxLength: 8,
              textInputAction: TextInputAction.go,
              onSubmitted: (_) => _checkCode(),
            ),
            const SizedBox(height: 16),

            // 验证按钮
            SizedBox(
              width: double.infinity,
              height: 48,
              child: FilledButton(
                onPressed: _checking ? null : _checkCode,
                child: _checking
                    ? const CircularProgressIndicator(strokeWidth: 2)
                    : const Text('验证邀请码'),
              ),
            ),

            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],

            // 会话信息
            if (_session != null) ...[
              const SizedBox(height: 32),
              const Divider(),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_session!['title'] ?? '面试会话',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      if (_session!['candidateName'] != null)
                        Text('候选人：${_session!['candidateName']}'),
                      Text('状态：${_session!['status'] == 'PENDING' ? '待录音' : _session!['status'] ?? '-'}'),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: () {
                            Navigator.pushNamed(context, '/record',
                                arguments: _session);
                          },
                          icon: const Icon(Icons.mic),
                          label: const Text('开始面试录音'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
