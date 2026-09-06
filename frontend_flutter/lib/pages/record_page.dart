import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/audio_service.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/services/websocket_service.dart';
import 'package:frontend_flutter/utils/helpers.dart';

class RecordPage extends StatefulWidget {
  final Function(Map<String, dynamic>)? onComplete;
  final String? questionTitle;
  final String? questionText;

  const RecordPage({
    super.key,
    this.onComplete,
    this.questionTitle,
    this.questionText,
  });

  @override
  State<RecordPage> createState() => _RecordPageState();
}

class _RecordPageState extends State<RecordPage>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  bool _isAnalyzing = false;
  bool _isUploading = false;
  bool _failed = false;
  String _failMessage = '';
  int _seconds = 0;
  int _progressPercent = 0;
  String _progressMessage = '正在上传音频...';
  Timer? _timer;
  Timer? _waveformTimer;
  late AnimationController _pulseCtrl;
  final _ws = WebSocketService();

  final List<double> _waveformHeights = List.generate(48, (_) => 4.0);

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _waveformTimer?.cancel();
    _pulseCtrl.dispose();
    _ws.dispose();
    AudioService.dispose();
    super.dispose();
  }

  void _startRecording() async {
    final hasPermission = await AudioService.requestMicPermission();
    if (!hasPermission) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AudioService.lastError ?? '需要麦克风权限才能录音'),
            backgroundColor: AppTheme.error,
            duration: const Duration(seconds: 4),
          ),
        );
      }
      return;
    }

    try {
      await AudioService.startRecord();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('启动录音失败: ${e.toString()}'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
      return;
    }
    _pulseCtrl.repeat();
    setState(() {
      _isRecording = true;
      _seconds = 0;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _seconds++);
    });
    _waveformTimer = Timer.periodic(const Duration(milliseconds: 120), (_) {
      if (!mounted) return;
      setState(() {
        for (int i = 0; i < _waveformHeights.length; i++) {
          _waveformHeights[i] = Random().nextDouble() * 38 + 6;
        }
      });
    });
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    _waveformTimer?.cancel();
    _pulseCtrl.stop();
    setState(() {
      _isRecording = false;
      _isUploading = true;
      _failed = false;
    });

    final bytes = await AudioService.stopRecord();
    if (bytes == null || !mounted) {
      setState(() => _isUploading = false);
      return;
    }

    try {
      // 1. 上传音频 → 后端建面试记录，返回 interview_id
      final result = await ApiService.uploadAudioBytes(bytes);
      if (!mounted) return;
      final interviewId = result['interview_id'] as int? ?? result['id'] as int? ?? 0;
      if (interviewId == 0) {
        throw Exception('上传成功但未返回面试记录');
      }

      setState(() {
        _isUploading = false;
        _isAnalyzing = true;
        _progressPercent = 5;
        _progressMessage = 'AI 分析中...';
      });

      // 2. 订阅 WS 实时进度（interview.{id}.progress/complete/error）
      _ws.onProgressChanged = (status, message) {
        if (!mounted) return;
        setState(() {
          _progressPercent = _ws.lastPercent;
          if (message != null) _progressMessage = message;
        });
      };
      await _ws.connect(interviewId: interviewId);

      // 3. 触发复盘分析（与 WS 推送同步，await 返回最终状态）
      final analysis = await ApiService.analyzeInterview(interviewId);
      if (!mounted) return;
      _ws.disconnect();

      if (analysis['status'] == 'COMPLETED') {
        final reportContent = await ApiService.getReportContent(interviewId);
        if (!mounted) return;
        final reportData = <String, dynamic>{
          'interview_id': interviewId,
          'report': reportContent,
          'recommendations': analysis['recommendations'] ?? const [],
        };
        widget.onComplete?.call(reportData);
        Navigator.pop(context);
      } else {
        final msg = analysis['status'] == 'FAILED'
            ? '分析失败，请重试'
            : '分析结果异常，请重试';
        setState(() {
          _isAnalyzing = false;
          _failed = true;
          _failMessage = msg;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isUploading = false;
        _isAnalyzing = false;
        _failed = true;
        _failMessage = '分析失败: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          onPressed: () {
            if (_isRecording) {
              _showExitDialog();
            } else {
              Navigator.pop(context);
            }
          },
        ),
        title: Text(widget.questionTitle ?? '面试录音',
            style: const TextStyle(color: AppTheme.textPrimary,
                fontWeight: FontWeight.w600)),
        centerTitle: true,
      ),
      body: SafeArea(
        child: _isUploading
            ? _buildUploadingState()
            : _isAnalyzing
                ? _buildAnalyzingState()
                : _failed
                    ? _buildFailedState()
                    : _buildRecordingState(),
      ),
    );
  }

  void _showExitDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16)),
        title: const Text('确认退出'),
        content: const Text('录音正在进行中，确定要退出吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('继续录音'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _timer?.cancel();
              _waveformTimer?.cancel();
              _pulseCtrl.stop();
              AudioService.dispose();
              Navigator.pop(context);
            },
            style: TextButton.styleFrom(
                foregroundColor: AppTheme.error),
            child: const Text('退出'),
          ),
        ],
      ),
    );
  }

  Widget _buildUploadingState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(
            width: 48, height: 48,
            child: CircularProgressIndicator(
              strokeWidth: 3, color: AppTheme.brand500,
            ),
          ),
          const SizedBox(height: 24),
          const Text('正在上传录音...',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Text('请稍候，正在上传到 AI 分析引擎',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }

  Widget _buildAnalyzingState() {
    final percent = _progressPercent.clamp(0, 100).toDouble();
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(
            width: 64, height: 64,
            child: CircularProgressIndicator(
              strokeWidth: 3, color: AppTheme.brand500,
            ),
          ),
          const SizedBox(height: 28),
          const Text('AI 正在分析面试内容...',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          Text(_progressMessage,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          const SizedBox(height: 12),
          Container(
            width: 220, height: 4,
            decoration: BoxDecoration(
              color: AppTheme.borderLight,
              borderRadius: BorderRadius.circular(2),
            ),
            child: FractionallySizedBox(
              widthFactor: percent / 100,
              child: Container(
                decoration: BoxDecoration(
                  color: AppTheme.brand500,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text('${percent.toInt()}%',
              style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
        ],
      ),
    );
  }

  /// 分析失败/异常态：可返回或重试
  Widget _buildFailedState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 56, color: AppTheme.error),
            const SizedBox(height: 20),
            const Text('分析未完成',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 8),
            Text(_failMessage,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('返回'),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() {
                      _failed = false;
                      _isAnalyzing = false;
                      _isUploading = false;
                    });
                  },
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('重新录音'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecordingState() {
    return Column(
      children: [
        const Spacer(flex: 1),
        if (widget.questionText != null) ...[
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.brand50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.brand100),
              ),
              child: Text(widget.questionText!,
                  style: const TextStyle(fontSize: 14,
                      color: AppTheme.textSecondary, height: 1.6)),
            ),
          ),
          const SizedBox(height: 16),
        ] else ...[
          const Text('AI 面试助手',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: AppTheme.brand500)),
          const SizedBox(height: 12),
        ],
        const Text('开始你的模拟面试',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary, letterSpacing: -0.5)),
        const SizedBox(height: 8),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 40),
          child: Text('点击下方按钮开始录音，AI 将实时分析你的回答并生成专业评估报告',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 15,
                  color: AppTheme.textSecondary, height: 1.5)),
        ),
        const Spacer(flex: 2),
        SizedBox(
          width: 220, height: 220,
          child: Stack(
            alignment: Alignment.center,
            children: [
              ...List.generate(
                  _isRecording ? 3 : 1, (i) => _buildPulseRing(i)),
              _buildMicButton(),
            ],
          ),
        ),
        const Spacer(flex: 1),
        SizedBox(
          height: 44,
          child: Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: List.generate(_waveformHeights.length, (i) {
                return Container(
                  width: 3,
                  height: _waveformHeights[i],
                  margin: const EdgeInsets.symmetric(horizontal: 1.5),
                  decoration: BoxDecoration(
                    color: AppTheme.brand400.withAlpha(179),
                    borderRadius: BorderRadius.circular(2),
                  ),
                );
              }),
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          AppHelpers.formatTime(_seconds),
          style: const TextStyle(
            fontSize: 36,
            fontWeight: FontWeight.w500,
            color: AppTheme.brand500,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: 10, height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isRecording ? AppTheme.error : AppTheme.success,
                boxShadow: _isRecording
                    ? [BoxShadow(
                        color: AppTheme.error.withAlpha(102),
                        blurRadius: 8)]
                    : null,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              _isRecording ? '正在录音中...' : '准备就绪 — 点击麦克风开始',
              style: TextStyle(
                fontSize: 14,
                color: _isRecording
                    ? AppTheme.error : AppTheme.textSecondary,
                fontWeight: _isRecording
                    ? FontWeight.w500 : FontWeight.normal,
              ),
            ),
          ],
        ),
        const Spacer(flex: 3),
      ],
    );
  }

  Widget _buildPulseRing(int index) {
    if (!_isRecording) {
      return Container(
        width: 220, height: 220,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: AppTheme.brand200.withAlpha(64),
            width: 1.0,
          ),
        ),
      );
    }
    return _PulseRingBuilder(
      listenable: _pulseCtrl,
      index: index,
    );
  }

  Widget _buildMicButton() {
    return GestureDetector(
      onTap: _isRecording ? _stopRecording : _startRecording,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        width: _isRecording ? 130 : 144,
        height: _isRecording ? 130 : 144,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: _isRecording ? AppTheme.error : AppTheme.brand500,
          boxShadow: [
            BoxShadow(
              color: _isRecording
                  ? const Color(0x1AC0524A)
                  : const Color(0x141B615B),
              blurRadius: 20,
              spreadRadius: 4,
            ),
          ],
        ),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: _isRecording
              ? const Icon(Icons.stop_rounded,
                  key: ValueKey('stop'), size: 48, color: Colors.white)
              : const Icon(Icons.mic_rounded,
                  key: ValueKey('mic'), size: 48, color: Colors.white),
        ),
      ),
    );
  }
}

class _PulseRingBuilder extends AnimatedWidget {
  final int index;
  const _PulseRingBuilder({
    required super.listenable,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    final animation = listenable as Animation<double>;
    final t = (animation.value + index * 0.25) % 1.0;
    final scale = 0.90 + t * 0.60;
    final opacity = (1.0 - t) * 0.35;
    return Transform.scale(
      scale: scale,
      child: Opacity(
        opacity: opacity,
        child: Container(
          width: 220, height: 220,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: AppTheme.brand200.withAlpha(77),
              width: 1.0,
            ),
          ),
        ),
      ),
    );
  }
}
