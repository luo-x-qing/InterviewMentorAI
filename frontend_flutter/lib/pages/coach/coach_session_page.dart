import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/coach_service.dart';
import 'package:frontend_flutter/services/websocket_service.dart';
import 'package:frontend_flutter/pages/coach/coach_report_page.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

/// 教练会话页：出题、文字作答、即时点评、循环、结课
///
/// 两种进入方式：
/// - 正常：从陪练主页开会话（sessionId 直达）
/// - 推荐练习：以推荐题为第一题开启会话（首题本地展示，后续出题走会话）
class CoachSessionPage extends StatefulWidget {
  final String? sessionId;
  final CoachQuestion? presetQuestion;

  const CoachSessionPage({
    super.key,
    this.sessionId,
    this.presetQuestion,
  });

  @override
  State<CoachSessionPage> createState() => _CoachSessionPageState();
}

class _CoachSessionPageState extends State<CoachSessionPage> {
  final _ws = WebSocketService();
  final _answerCtrl = TextEditingController();

  String? _sessionId;
  CoachQuestion? _question;
  bool _isPresetFirst = false;
  bool _loading = true;
  bool _submitting = false;
  String? _error;

  CoachFeedback? _feedback;

  @override
  void initState() {
    super.initState();
    _sessionId = widget.sessionId;
    _load();
  }

  @override
  void dispose() {
    _ws.dispose();
    _answerCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // 推荐练习：先开会话，首题用推荐题，后续出题走会话
      if (widget.presetQuestion != null && _sessionId == null) {
        final handle = await CoachService.startSession(mode: 'TEXT', difficulty: 'MEDIUM');
        _sessionId = handle['session_id'] as String;
        _isPresetFirst = true;
      }
      if (_sessionId == null) {
        throw Exception('会话尚未创建');
      }
      _question = _isPresetFirst ? widget.presetQuestion : await CoachService.nextQuestion(_sessionId!);
      _subscribeWs();
      if (!mounted) return;
      setState(() => _loading = false);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  void _subscribeWs() {
    final sid = _sessionId;
    if (sid == null) return;
    _ws.onCoachFeedback = (payload) {
      if (!mounted) return;
      setState(() {
        _feedback = CoachFeedback(
          isCorrect: payload['is_correct'] as bool? ?? false,
          score: payload['score'] as int? ?? 0,
          feedback: payload['feedback'] as String? ?? '',
          correctAnswer: payload['correct_answer'] as String? ?? '',
        );

      });
    };
    _ws.connect(coachSessionId: sid);
  }

  Future<void> _submit() async {
    final sid = _sessionId;
    final answer = _answerCtrl.text.trim();
    if (sid == null || answer.isEmpty || _submitting) return;
    setState(() => _submitting = true);
    try {
      final feedback = await CoachService.submitAnswer(sid, answer);
      if (!mounted) return;
      setState(() {
        _feedback = feedback;
        _submitting = false;

      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('提交失败: $e'), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<void> _next() async {
    final sid = _sessionId;
    if (sid == null || _loading) return;
    setState(() {
      _loading = true;
      _feedback = null;
      _answerCtrl.clear();
    });
    try {
      final question = await CoachService.nextQuestion(sid);
      if (!mounted) return;
      setState(() {
        _question = question;
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

  Future<void> _finish() async {
    final sid = _sessionId;
    if (sid == null || _loading) return;
    setState(() => _loading = true);
    try {
      final report = await CoachService.endSession(sid);
      if (!mounted) return;
      _ws.disconnect();
      final changed = await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CoachReportPage(report: report),
        ),
      );
      if (!mounted) return;
      if (changed == true) {
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('结课失败: $e'), backgroundColor: AppTheme.error),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        title: const Text('陪练会话'),
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          onPressed: () {
            if (_feedback != null || _question != null) {
              _confirmExit();
            } else {
              Navigator.pop(context);
            }
          },
        ),
        actions: [
          TextButton(
            onPressed: _feedback != null ? _finish : null,
            child: const Text('结课'),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: AppTheme.brand500))
            : _error != null
                ? _buildError()
                : _buildSession(),
      ),
    );
  }

  void _confirmExit() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('结束陪练'),
        content: const Text('会话仍在进行中，退出将无法生成结课报告。确定退出吗'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('继续陪练'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pop(context);
            },
            style: TextButton.styleFrom(foregroundColor: AppTheme.error),
            child: const Text('退出'),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: EmptyStateWidget(
        icon: Icons.error_outline,
        title: '会话加载失败',
        subtitle: _error,
        action: ElevatedButton.icon(
          onPressed: _load,
          icon: const Icon(Icons.refresh, size: 18),
          label: const Text('重试'),
        ),
      ),
    );
  }

  Widget _buildSession() {
    final q = _question;
    if (q == null) return const SizedBox.shrink();
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: AppTheme.brand50,
                  borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                ),
                child: Text(q.difficulty,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500,
                        color: AppTheme.brand500)),
              ),
              const Spacer(),
              const Text('文字作答 · 即时点评',
                  style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: AppTheme.cardDecoration,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(q.title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary, letterSpacing: -0.02)),
                const SizedBox(height: 12),
                Text(q.question,
                    style: const TextStyle(fontSize: 15,
                        color: AppTheme.textSecondary, height: 1.7)),
                if (q.evaluationPoints.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text('考察点：${q.evaluationPoints}',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_feedback == null)
            _buildAnswerInput()
          else
            _buildFeedbackCard(),
          const SizedBox(height: 16),
          if (_feedback != null)
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _next,
                    icon: const Icon(Icons.arrow_forward, size: 18),
                    label: const Text('下一题'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _finish,
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('完成结课'),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildAnswerInput() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('你的回答',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 10),
          TextField(
            controller: _answerCtrl,
            minLines: 4,
            maxLines: 8,
            maxLength: 4000,
            decoration: const InputDecoration(
              hintText: '输入你的回答，尽量完整展开思路...',
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.send, size: 18),
              label: Text(_submitting ? '点评中...' : '提交点评'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackCard() {
    final fb = _feedback!;
    final correct = fb.isCorrect;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: correct ? AppTheme.successBg : AppTheme.warningBg,
        borderRadius: BorderRadius.circular(AppTheme.radiusLg),
        border: Border.all(
            color: correct ? AppTheme.success.withValues(alpha: 0.4)
                : AppTheme.warning.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(correct ? Icons.check_circle : Icons.info_outline,
                  size: 22, color: correct ? AppTheme.success : AppTheme.warning),
              const SizedBox(width: 8),
              Text(correct ? '回答正确' : '仍需打磨',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600,
                      color: correct ? AppTheme.success : AppTheme.warning)),
              const Spacer(),
              Text('${fb.score} 分',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                      color: correct ? AppTheme.success : AppTheme.warning)),
            ],
          ),
          const SizedBox(height: 10),
          Text(fb.feedback,
              style: const TextStyle(fontSize: 14,
                  color: AppTheme.textSecondary, height: 1.6)),
          if (fb.correctAnswer.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.bgCard.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              ),
              child: Text('参考答案：${fb.correctAnswer}',
                  style: const TextStyle(fontSize: 13,
                      color: AppTheme.textSecondary, height: 1.5)),
            ),
          ],
        ],
      ),
    );
  }
}
