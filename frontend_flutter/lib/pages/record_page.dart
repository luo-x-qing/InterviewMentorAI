import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/services/audio_service.dart';
import 'package:frontend_flutter/services/api_service.dart';

class RecordPage extends StatefulWidget {
  const RecordPage({super.key});

  @override
  State<RecordPage> createState() => _RecordPageState();
}

class _RecordPageState extends State<RecordPage>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  bool _isAnalyzing = false;
  int _seconds = 0;
  Timer? _timer;
  Timer? _waveformTimer;
  late AnimationController _pulseCtrl;

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
    AudioService.dispose();
    super.dispose();
  }

  String _formatTime(int s) {
    final m = (s ~/ 60).toString().padLeft(2, '0');
    final sec = (s % 60).toString().padLeft(2, '0');
    return '$m:$sec';
  }

  void _startRecording() async {
    await AudioService.startRecord();
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
      _isAnalyzing = true;
    });
    final path = await AudioService.stopRecord();
    if (path != null && mounted) {
      try {
        final result = await ApiService.uploadAudioFile(path);
        if (mounted) {
          Navigator.pushReplacementNamed(context, '/report',
              arguments: result['data']);
        }
      } catch (_) {
        if (mounted) {
          setState(() => _isAnalyzing = false);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('上传失败，请重试')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: _isAnalyzing ? _buildAnalyzing() : _buildRecording(),
      ),
    );
  }

  Widget _buildAnalyzing() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 72, height: 72,
            child: CircularProgressIndicator(
              strokeWidth: 3,
              valueColor: const AlwaysStoppedAnimation(AppTheme.brand500),
            ),
          ),
          const SizedBox(height: 28),
          const Text('AI 正在分析面试内容...',
              style: TextStyle(fontSize: 16, color: AppTheme.textSecondary)),
          const SizedBox(height: 8),
          const Text('请稍候，这可能需要 1-2 分钟',
              style: TextStyle(fontSize: 13, color: AppTheme.textMuted)),
        ],
      ),
    );
  }

  Widget _buildRecording() {
    return Column(
      children: [
        const Spacer(flex: 2),
        // Section label
        const Text(
          'AI 面试助手',
          style: TextStyle(
            fontSize: 12, fontWeight: FontWeight.w600,
            letterSpacing: 1.2, color: AppTheme.brand500,
          ),
        ),
        const SizedBox(height: 12),
        const Text(
          '开始你的模拟面试',
          style: TextStyle(
            fontSize: 28, fontWeight: FontWeight.w600,
            color: AppTheme.textPrimary, letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 8),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 40),
          child: Text(
            '点击下方按钮开始录音，AI 将实时分析你的回答并生成专业评估报告',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, color: AppTheme.textSecondary, height: 1.5),
          ),
        ),
        const Spacer(flex: 2),

        // Mic button
        SizedBox(
          width: 220, height: 220,
          child: Stack(
            alignment: Alignment.center,
            children: [
              ...List.generate(_isRecording ? 3 : 1, (i) => _buildPulseRing(i)),
              _buildMicButton(),
            ],
          ),
        ),

        const Spacer(flex: 1),

        // Waveform
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
                    color: AppTheme.brand400.withValues(alpha: 0.7),
                    borderRadius: BorderRadius.circular(2),
                  ),
                );
              }),
            ),
          ),
        ),

        const SizedBox(height: 20),

        // Timer
        Text(
          _formatTime(_seconds),
          style: const TextStyle(
            fontSize: 36,
            fontWeight: FontWeight.w500,
            color: AppTheme.brand500,
            fontFeatures: [FontFeature.tabularFigures()],
          ),
        ),
        const SizedBox(height: 16),

        // Status
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 10, height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isRecording ? AppTheme.success : AppTheme.textMuted,
                boxShadow: _isRecording
                    ? [BoxShadow(color: AppTheme.success.withValues(alpha: 0.4), blurRadius: 8)]
                    : null,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              _isRecording ? '正在录音中...' : '准备就绪 — 点击麦克风开始',
              style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
            ),
          ],
        ),
        const Spacer(flex: 3),
      ],
    );
  }

  Widget _buildPulseRing(int index) {
    if (!_isRecording) {
      // Idle: 一枚静置淡蓝细环
      return Container(
        width: 220, height: 220,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: AppTheme.brand200.withValues(alpha: 0.25),
            width: 1.0,
          ),
        ),
      );
    }
    return _PulseRingBuilder(
      animation: _pulseCtrl,
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
          gradient: LinearGradient(
            colors: _isRecording
                ? [const Color(0xFFEF4444), const Color(0xFFDC2626)]
                : [AppTheme.gradientStart, AppTheme.gradientEnd],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          boxShadow: [
            BoxShadow(
              color: _isRecording
                  ? const Color(0x1AEF4444)
                  : const Color(0x1A4F46E5),
              blurRadius: _isRecording ? 40 : 32,
              spreadRadius: _isRecording ? 12 : 8,
            ),
          ],
        ),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: _isRecording
              ? const Icon(Icons.stop_rounded, key: ValueKey('stop'),
                  size: 48, color: Colors.white)
              : const Icon(Icons.mic_rounded, key: ValueKey('mic'),
                  size: 48, color: Colors.white),
        ),
      ),
    );
  }
}

class _PulseRingBuilder extends AnimatedWidget {
  final int index;
  const _PulseRingBuilder({
    super.key,
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
              color: AppTheme.brand200.withValues(alpha: 0.3),
              width: 1.0,
            ),
          ),
        ),
      ),
    );
  }
}
