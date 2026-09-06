import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/pages/report_page.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

/// 面试记录列表页
class InterviewHistoryPage extends StatefulWidget {
  const InterviewHistoryPage({super.key});

  @override
  State<InterviewHistoryPage> createState() => _InterviewHistoryPageState();
}

class _InterviewHistoryPageState extends State<InterviewHistoryPage> {
  final List<Map<String, dynamic>> _reports = [];
  bool _loading = true;
  bool _loadFailed = false;

  @override
  void initState() {
    super.initState();
    _loadReports();
  }

  Future<void> _loadReports() async {
    setState(() => _loading = true);
    try {
      final reports = await ApiService.getReportList();
      final mapped = reports.map((e) => {
            'interview_id': e['interview_id'],
            'title': _titleOf(e['content'] as String? ?? ''),
            'date': (e['created_at'] as String? ?? '').split('T').first,
            'report': e['content'] as String? ?? '',
          }).toList();
      setState(() {
        _reports
          ..clear()
          ..addAll(mapped);
        _loadFailed = false;
      });
    } catch (e) {
      setState(() => _loadFailed = true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _titleOf(String content) {
    final line = content
        .split('\n')
        .map((l) => l.trim())
        .firstWhere((l) => l.isNotEmpty, orElse: () => '');
    final title = line.replaceFirst(RegExp(r'^#+\s*'), '');
    return title.isNotEmpty ? title : '面试报告';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(title: const Text('面试记录')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
          : _reports.isEmpty
              ? EmptyStateWidget(
                  icon: _loadFailed ? Icons.cloud_off : Icons.history,
                  title: _loadFailed ? '加载失败' : '暂无面试记录',
                  subtitle: _loadFailed ? '请检查网络后下拉重试' : '完成一次模拟面试后，报告将显示在这里',
                  action: _loadFailed
                      ? TextButton(onPressed: _loadReports, child: const Text('重试'))
                      : null,
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    await _loadReports();
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                    itemCount: _reports.length,
                    itemBuilder: (context, index) {
                      return _buildReportCard(_reports[index], index);
                    },
                  ),
                ),
    );
  }

  Widget _buildReportCard(Map<String, dynamic> report, int index) {
    final title = (report['title'] as String?) ?? '面试报告';
    final date = (report['date'] as String?) ?? '';
    final interviewId =
        (report['interview_id'] as num?)?.toInt() ?? index + 1;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: AppTheme.cardDecoration,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {
            Navigator.push(context,
                MaterialPageRoute(builder: (_) => ReportPage(data: report)));
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    color: AppTheme.brand500,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Center(
                    child: Text('${index + 1}',
                        style: const TextStyle(color: Colors.white,
                            fontWeight: FontWeight.w600, fontSize: 18)),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title,
                          style: const TextStyle(fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 4),
                      Text('$date  ·  报告 #$interviewId',
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
