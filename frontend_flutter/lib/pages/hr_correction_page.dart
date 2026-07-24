import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/services/token_storage.dart';
import 'package:frontend_flutter/utils/constants.dart';

/// HR 人工修正评估页面
///
/// 加载指定面试的逐条评估列表，支持修改分数、等级和评语。
/// 调用 PUT /report/evaluation/{id}/correct 逐条提交修正。
class HrCorrectionPage extends StatefulWidget {
  final int interviewId;

  const HrCorrectionPage({super.key, required this.interviewId});

  @override
  State<HrCorrectionPage> createState() => _HrCorrectionPageState();
}

class _HrCorrectionPageState extends State<HrCorrectionPage> {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: Constants.baseUrl,
    connectTimeout: const Duration(seconds: 10),
  ));

  List<Map<String, dynamic>> _evaluations = [];
  bool _loading = true;
  String? _error;

  // 编辑中的修正数据: evalId → {score, level, remark}
  final Map<int, Map<String, dynamic>> _edits = {};

  @override
  void initState() {
    super.initState();
    _loadEvaluations();
  }

  Future<void> _loadEvaluations() async {
    setState(() { _loading = true; _error = null; });
    try {
      final token = TokenStorage.accessToken;
      final resp = await _dio.get(
        '${Constants.reportEvaluationsApi}/${widget.interviewId}/evaluations',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      final data = resp.data;
      if (data['code'] == 200) {
        setState(() => _evaluations = List<Map<String, dynamic>>.from(data['data'] ?? []));
      } else {
        setState(() => _error = data['message'] ?? '加载失败');
      }
    } catch (e) {
      setState(() => _error = '加载失败：$e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _submitCorrection(int evalId) async {
    final edit = _edits[evalId];
    if (edit == null) return;

    try {
      final token = TokenStorage.accessToken;
      final body = <String, dynamic>{
        'evaluationId': evalId,
      };
      if (edit.containsKey('hrScore')) body['hrScore'] = edit['hrScore'];
      if (edit.containsKey('hrLevel')) body['hrLevel'] = edit['hrLevel'];
      if (edit.containsKey('hrRemark')) body['hrRemark'] = edit['hrRemark'];

      await _dio.put(
        '${Constants.reportCorrectEvalApi}/$evalId/correct',
        data: body,
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('修正已保存'), duration: Duration(seconds: 1)),
      );
      _edits.remove(evalId);
      _loadEvaluations(); // 刷新
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('保存失败：$e'), backgroundColor: Colors.red),
      );
    }
  }

  void _showEditDialog(int index) {
    final eval = _evaluations[index];
    final evalId = eval['id'] as int;
    final existing = _edits[evalId] ?? {};

    final scoreCtrl = TextEditingController(
        text: (existing['hrScore'] ?? eval['aiScore'] ?? '').toString());
    final remarkCtrl = TextEditingController(
        text: (existing['hrRemark'] ?? eval['hrRemark'] ?? '').toString());
    String level = (existing['hrLevel'] ?? eval['hrLevel'] ?? eval['aiLevel'] ?? '一般').toString();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text('修正评估 #${index + 1}'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(eval['question'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('回答：${eval['answer'] ?? '（无）'}',
                    style: const TextStyle(color: Colors.grey, fontSize: 13)),
                const Divider(height: 20),
                TextField(
                  controller: scoreCtrl,
                  decoration: const InputDecoration(
                    labelText: 'HR 评分 (0-100)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: level,
                  decoration: const InputDecoration(
                    labelText: '等级',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: ['优秀', '良好', '一般', '较差']
                      .map((l) => DropdownMenuItem(value: l, child: Text(l)))
                      .toList(),
                  onChanged: (v) {
                    if (v != null) {
                      setDialogState(() => level = v);
                    }
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: remarkCtrl,
                  decoration: const InputDecoration(
                    labelText: 'HR 评语',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  maxLines: 3,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
            FilledButton(
              onPressed: () {
                final newEdit = <String, dynamic>{};
                final s = double.tryParse(scoreCtrl.text);
                if (s != null) newEdit['hrScore'] = s;
                newEdit['hrLevel'] = level;
                if (remarkCtrl.text.isNotEmpty) newEdit['hrRemark'] = remarkCtrl.text;
                setState(() => _edits[evalId] = newEdit);
                Navigator.pop(ctx);
                _submitCorrection(evalId);
              },
              child: const Text('保存修正'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('HR 评估修正')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _evaluations.length,
                  itemBuilder: (context, index) {
                    final e = _evaluations[index];
                    final evalId = e['id'] as int;
                    final hasEdit = _edits.containsKey(evalId);
                    return Card(
                      color: hasEdit ? Colors.amber.withValues(alpha: 0.05) : null,
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        title: Text('Q${index + 1}: ${e['question'] ?? ''}',
                            maxLines: 2, overflow: TextOverflow.ellipsis),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('AI 评分: ${e['aiScore'] ?? '-'} | 等级: ${e['aiLevel'] ?? '-'}'),
                            if (hasEdit) const Text('📝 已修改', style: TextStyle(color: Colors.amber)),
                          ],
                        ),
                        trailing: FilledButton.tonal(
                          onPressed: () => _showEditDialog(index),
                          child: const Text('修正'),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
