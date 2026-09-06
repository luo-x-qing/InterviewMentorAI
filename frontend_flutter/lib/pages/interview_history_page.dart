import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/utils/helpers.dart';
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
  bool _hasMore = true;
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
    _loadReports();
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels > _scrollCtrl.position.maxScrollExtent * 0.8) {
      _loadMore();
    }
  }

  Future<void> _loadReports() async {
    // 使用模拟数据（后续接入 /report/list API）
    await Future.delayed(const Duration(milliseconds: 600));
    _addMockReports();
    setState(() => _loading = false);
  }

  void _addMockReports() {
    _reports.addAll([
      {'id': 'R001', 'score': 85, 'date': '2026-07-30', 'title': '高级前端工程师面试'},
      {'id': 'R002', 'score': 72, 'date': '2026-07-28', 'title': '全栈工程师面试'},
      {'id': 'R003', 'score': 92, 'date': '2026-07-25', 'title': '前端实习生面试'},
      {'id': 'R004', 'score': 78, 'date': '2026-07-20', 'title': 'React 专场面试'},
      {'id': 'R005', 'score': 68, 'date': '2026-07-15', 'title': '系统设计面试'},
      {'id': 'R006', 'score': 88, 'date': '2026-07-10', 'title': '算法专场面试'},
    ]);
  }

  Future<void> _loadMore() async {
    if (!_hasMore || _loading) return;
    // 模拟分页 — 第二页后无更多数据
    await Future.delayed(const Duration(milliseconds: 400));
    setState(() => _hasMore = false);
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
                  icon: Icons.history,
                  title: '暂无面试记录',
                  subtitle: '完成一次模拟面试后，报告将显示在这里',
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    _reports.clear();
                    _hasMore = true;
                    await _loadReports();
                  },
                  child: ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                    itemCount: _reports.length + (_hasMore ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == _reports.length) {
                        return const Padding(
                          padding: EdgeInsets.all(20),
                          child: Center(child: CircularProgressIndicator(
                              color: AppTheme.brand500, strokeWidth: 2)),
                        );
                      }
                      return _buildReportCard(_reports[index], index);
                    },
                  ),
                ),
    );
  }

  Widget _buildReportCard(Map<String, dynamic> report, int index) {
    final score = report['score'] as int;
    final grade = AppHelpers.gradeLabel(score);

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
                      Text(report['title'] as String,
                          style: const TextStyle(fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 4),
                      Text('${report['date']}  ·  $score 分 · $grade',
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
