import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// 首页：历史面试记录列表 + 录音入口
///
/// 下拉刷新加载列表，点击条目跳转报告详情。
/// FAB 进入录音页面（自主录音）或邀请码页面（HR 邀请）。
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: const Duration(seconds: 10),
  ));

  List<Map<String, dynamic>> _records = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  Future<void> _loadRecords() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final resp = await _dio.get(Constants.recordListApi);
      final data = resp.data;
      if (data['code'] == 200) {
        final list = (data['data']?['records'] ?? data['data']) as List? ?? [];
        setState(() => _records = list.cast<Map<String, dynamic>>());
      } else {
        setState(() => _error = data['message'] ?? '加载失败');
      }
    } catch (e) {
      setState(() => _error = '网络错误：$e');
    } finally {
      setState(() => _loading = false);
    }
  }

  /// 状态标签样式
  Widget _statusChip(String? status) {
    final label = switch (status) {
      'COMPLETED' => '已完成',
      'PROCESSING' => '分析中',
      'FAILED' => '失败',
      'CREATED' => '待分析',
      _ => status ?? '未知',
    };
    final color = switch (status) {
      'COMPLETED' => Colors.green,
      'PROCESSING' => Colors.orange,
      'FAILED' => Colors.red,
      _ => Colors.grey,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('InterviewMentorAI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.login),
            tooltip: '邀请码',
            onPressed: () => Navigator.pushNamed(context, '/invite'),
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/record'),
        child: const Icon(Icons.mic),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 12),
            FilledButton.tonal(onPressed: _loadRecords, child: const Text('重试')),
          ],
        ),
      );
    }

    if (_records.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 120),
          const Icon(Icons.history, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('暂无面试记录', textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 16)),
          const SizedBox(height: 8),
          const Text('点击右下角麦克风开始录音', textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 13)),
        ],
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRecords,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        itemCount: _records.length,
        itemBuilder: (context, index) {
          final r = _records[index];
          final title = r['title'] ?? '面试记录 #${r['id']}';
          final jobRole = r['jobRole'] as String?;
          final status = r['status'] as String?;
          final createdAt = r['createdAt'] as String? ?? '';

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 5),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: const Icon(Icons.description_outlined),
              ),
              title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Row(
                children: [
                  if (jobRole != null && jobRole.isNotEmpty) ...[
                    Text(jobRole, style: const TextStyle(fontSize: 13)),
                    const SizedBox(width: 8),
                  ],
                  _statusChip(status),
                ],
              ),
              trailing: Text(
                createdAt.length >= 10 ? createdAt.substring(0, 10) : createdAt,
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              onTap: () {
                Navigator.pushNamed(context, '/report', arguments: r);
              },
            ),
          );
        },
      ),
    );
  }
}
