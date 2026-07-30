import 'dart:async';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/pages/record_page.dart';
import 'package:frontend_flutter/pages/report_page.dart';
import 'package:frontend_flutter/services/audio_service.dart';
import 'package:frontend_flutter/services/api_service.dart';

enum _StepRecordStatus { pending, processing, completed }

class _StepRecord {
  _StepRecordStatus status = _StepRecordStatus.pending;
  Map<String, dynamic>? reportData;
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int _currentTab = 0;
  int _currentStep = 0;

  List<Map<String, dynamic>>? _reports;
  List<_StepRecord> _stepRecords = [];

  // Embedded recording state
  bool _isRecording = false;
  int _recordSeconds = 0;
  Timer? _recordTimer;
  Timer? _waveformTimer;
  final List<double> _waveformHeights = List.generate(48, (_) => 4.0);

  final _steps = const [
    _StepData('自我介绍', '~2 分钟',
        '请做一个简短的自我介绍，包括你的背景、核心技能以及为什么你对这个职位感兴趣。',
        '控制在 1-2 分钟内，突出 3 个最相关的技能或经历。'),
    _StepData('技术能力', '~5 分钟',
        '请描述你在前端开发中遇到的最复杂的技术挑战，以及你是如何解决的。涉及哪些技术栈和架构决策？',
        '使用 STAR 法则（情境→任务→行动→结果）结构化你的回答。'),
    _StepData('项目经验', '~5 分钟',
        '假设你要从零搭建一个 SaaS 平台，你会如何设计技术架构？请考虑可扩展性、安全性和团队协作。',
        '从数据层、服务层、前端层分别阐述，展示全栈思维。'),
    _StepData('情景分析', '~3 分钟',
        '产品经理要求在两周内上线一个紧急功能，但技术评估需要四周。你会如何处理这种冲突？',
        '展示你的沟通能力、优先级判断和折中方案设计能力。'),
    _StepData('总结提问', '~2 分钟',
        '回顾今天的面试，你觉得哪些方面表现得最好？有什么你希望补充说明的吗？另外，你有什么问题想问我？',
        '这是最后的机会留下深刻印象，准备 1-2 个有深度的问题反问面试官。'),
  ];

  @override
  void initState() {
    super.initState();
    _reports = [];
    _stepRecords = List.generate(_steps.length, (_) => _StepRecord());
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        setState(() => _currentTab = _tabController.index);
      }
    });
  }

  @override
  void dispose() {
    _recordTimer?.cancel();
    _waveformTimer?.cancel();
    AudioService.dispose();
    _tabController.dispose();
    super.dispose();
  }

  String _formatTime(int s) {
    final m = (s ~/ 60).toString().padLeft(2, '0');
    final sec = (s % 60).toString().padLeft(2, '0');
    return '$m:$sec';
  }

  // ──── 嵌入录音 ────

  Future<void> _startStepRecording() async {
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
            content: Text('启动录音失败: $e'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
      return;
    }

    setState(() {
      _isRecording = true;
      _recordSeconds = 0;
    });

    _recordTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _recordSeconds++);
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

  Future<void> _stopStepRecording() async {
    _recordTimer?.cancel();
    _waveformTimer?.cancel();
    setState(() => _isRecording = false);

    final bytes = await AudioService.stopRecord();
    if (bytes == null) return;

    _stepRecords[_currentStep].status = _StepRecordStatus.processing;
    _uploadStepAudio(_currentStep, bytes);

    if (_currentStep < _steps.length - 1) {
      setState(() => _currentStep++);
    } else {
      _finalizeInterview();
    }
  }

  Future<void> _uploadStepAudio(int step, Uint8List bytes) async {
    try {
      final result = await ApiService.uploadAudioBytes(bytes);
      final data = result['data'] as Map<String, dynamic>?;
      if (mounted) {
        setState(() {
          _stepRecords[step].reportData = data;
          _stepRecords[step].status = _StepRecordStatus.completed;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _stepRecords[step].status = _StepRecordStatus.pending;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('第 ${step + 1} 步上传失败: $e'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    }
  }

  Future<void> _finalizeInterview() async {
    final pending = _stepRecords.where((r) =>
        r.status == _StepRecordStatus.processing).toList();
    if (pending.isNotEmpty && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('正在等待所有步骤的分析结果...'),
          backgroundColor: AppTheme.brand500,
          duration: Duration(seconds: 2),
        ),
      );
      for (final _ in pending) {
        await Future.delayed(const Duration(seconds: 2));
      }
    }

    final merged = <String, dynamic>{};
    for (final r in _stepRecords) {
      if (r.reportData != null) merged.addAll(r.reportData!);
    }
    _onRecordingComplete(merged);
  }

  // ──── 录音回调 ────

  void _onRecordingComplete(Map<String, dynamic> reportData) {
    setState(() {
      if (reportData.isNotEmpty) (_reports ??= []).add(reportData);
    });
    _showReportReadyDialog();
  }

  void _showReportReadyDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.successBg,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.check_circle,
                  color: AppTheme.success, size: 28),
            ),
            const SizedBox(width: 12),
            const Text('报告生成完成'),
          ],
        ),
        content: const Text(
          'AI 已为你完成面试分析，点击下方按钮查看详细评估报告。',
          style: TextStyle(fontSize: 15, height: 1.6),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _tabController.animateTo(2);
            },
            child: const Text('稍后查看'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ReportPage(
                      data: _reports != null && _reports!.isNotEmpty
                          ? _reports!.last
                          : null),
                ),
              );
            },
            child: const Text('查看报告'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      body: SafeArea(
        child: Column(
          children: [
            _buildCapsuleTabs(),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                physics: const BouncingScrollPhysics(),
                children: [
                  _buildRecordTab(),
                  _buildInterviewTab(),
                  _buildReportTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCapsuleTabs() {
    const tabs = ['录音', '面试流程', '评估报告'];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: BorderRadius.circular(AppTheme.radiusFull),
          border: Border.all(color: AppTheme.borderLight),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0D000000),
              blurRadius: 8,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: List.generate(3, (index) {
            final active = _currentTab == index;
            return Expanded(
              child: GestureDetector(
                onTap: () => _tabController.animateTo(index),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 240),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    gradient:
                        active ? AppTheme.gradientPrimary : null,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                  ),
                  child: Text(
                    tabs[index],
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color:
                          active ? Colors.white : AppTheme.textSecondary,
                    ),
                  ),
                ),
              ),
            );
          }),
        ),
      ),
    );
  }

  // ──────────── Tab 1: 录音 ────────────
  Widget _buildRecordTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
            decoration: BoxDecoration(
              color: AppTheme.brand50,
              borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            ),
            child: const Text('AI 面试助手',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                    color: AppTheme.brand500, letterSpacing: 1.2)),
          ),
          const SizedBox(height: 16),
          const Text('开始你的模拟面试',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary, letterSpacing: -0.04)),
          const SizedBox(height: 10),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text('点击下方按钮开始录音，AI 将实时分析你的回答并生成专业评估报告',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15,
                    color: AppTheme.textSecondary, height: 1.6)),
          ),
          const SizedBox(height: 48),
          GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => RecordPage(
                    onComplete: _onRecordingComplete,
                  ),
                ),
              );
            },
            child: Container(
              width: 144,
              height: 144,
              decoration: AppTheme.glowDecoration,
              child: const Icon(Icons.mic_rounded, size: 52, color: Colors.white),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 8, height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.success,
                  boxShadow: [
                    BoxShadow(color: AppTheme.success.withAlpha(89), blurRadius: 8),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              const Text('准备就绪 — 点击麦克风开始',
                  style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
            ],
          ),
          const SizedBox(height: 32),
          if (_reports != null && _reports!.isNotEmpty && mounted) _buildRecentReportEntry(),
          const SizedBox(height: 48),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: AppTheme.brand50.withAlpha(128),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.brand100),
            ),
            child: Row(
              children: [
                Icon(Icons.lightbulb_outline,
                    color: AppTheme.brand500, size: 20),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text('建议准备 3-5 分钟的回答，涵盖核心技能与项目经验',
                      style: TextStyle(fontSize: 13,
                          color: AppTheme.textSecondary, height: 1.5)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildRecentReportEntry() {
    final report = _reports == null || _reports!.isEmpty
        ? ReportPage.mockData() : _reports!.last;
    final score = report['score'] as int? ?? 0;
    final grade = score >= 90 ? '卓越' : score >= 80 ? '优秀'
        : score >= 70 ? '良好' : score >= 60 ? '一般' : '待提高';
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.brand50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.brand100),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.description_outlined,
                color: AppTheme.brand500, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('面试报告 — $score 分 ($grade)',
                    style: const TextStyle(fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary)),
                Text('点击查看详细评估',
                    style: TextStyle(fontSize: 12,
                        color: AppTheme.textSecondary)),
              ],
            ),
          ),
          IconButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ReportPage(data: report),
                ),
              );
            },
            icon: const Icon(Icons.arrow_forward_ios, size: 16),
            color: AppTheme.brand500,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }

  // ──────────── Tab 2: 面试流程 ────────────
  Widget _buildInterviewTab() {
    final step = _steps[_currentStep];
    final record = _stepRecords[_currentStep];

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('分步引导 · 精准评估',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary, letterSpacing: -0.03)),
                SizedBox(height: 6),
                Text('从自我介绍到情景分析，AI 引导你完成完整的面试模拟',
                    style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 68,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _steps.length,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (context, index) {
                final active = index == _currentStep;
                final sr = _stepRecords[index];
                final done = sr.status == _StepRecordStatus.completed;
                final processing = sr.status == _StepRecordStatus.processing;
                return GestureDetector(
                  onTap: () => setState(() => _currentStep = index),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: active ? AppTheme.brand50
                          : done ? AppTheme.successBg : Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: active ? AppTheme.brand100
                            : done ? AppTheme.success : AppTheme.borderLight,
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 28, height: 28,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: done ? AppTheme.success
                                : processing ? AppTheme.warning
                                : active ? AppTheme.brand50 : AppTheme.bgPage,
                            border: Border.all(
                              color: done ? Colors.transparent
                                  : processing ? AppTheme.warning
                                  : active ? AppTheme.brand500 : AppTheme.borderLight,
                              width: 2,
                            ),
                          ),
                          child: Center(
                            child: done
                                ? const Icon(Icons.check, size: 16,
                                    color: Colors.white)
                                : processing
                                ? const SizedBox(
                                    width: 14, height: 14,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: AppTheme.warning,
                                    ),
                                  )
                                : Text('${index + 1}',
                                    style: TextStyle(fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: active
                                            ? AppTheme.brand500
                                            : AppTheme.textMuted)),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(_steps[index].name,
                                style: TextStyle(fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                    color: active
                                        ? AppTheme.textPrimary
                                        : AppTheme.textSecondary)),
                            Text(done ? '已完成'
                                : processing ? '分析中'
                                : _steps[index].duration,
                                style: TextStyle(fontSize: 11,
                                    color: done ? AppTheme.success
                                        : processing ? AppTheme.warning
                                        : AppTheme.textMuted)),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(24),
            decoration: AppTheme.cardDecoration,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(step.name,
                    style: const TextStyle(fontSize: 20,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary, letterSpacing: -0.03)),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.brand50,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                  ),
                  child: Text('步骤 ${_currentStep + 1}/${_steps.length}',
                      style: const TextStyle(fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.brand500)),
                ),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.bgPage,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Text(step.question,
                      style: const TextStyle(fontSize: 15,
                          color: AppTheme.textSecondary, height: 1.7)),
                ),
                const SizedBox(height: 16),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.lightbulb_outline,
                        color: AppTheme.textMuted, size: 18),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text('提示：${step.tip}',
                          style: const TextStyle(fontSize: 13,
                              color: AppTheme.textSecondary, height: 1.5)),
                    ),
                  ],
                ),

                // ──── 嵌入录音 UI ────
                if (_isRecording) ...[
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 14),
                    decoration: BoxDecoration(
                      color: AppTheme.brand50,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      children: [
                        Text(_formatTime(_recordSeconds),
                            style: const TextStyle(fontSize: 32,
                                fontWeight: FontWeight.w500,
                                color: AppTheme.brand500,
                                fontFeatures: [FontFeature.tabularFigures()])),
                        const SizedBox(height: 8),
                        SizedBox(
                          height: 28,
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
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
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 24),

                // ──── 按钮 ────
                if (_isRecording) ...[
                  Row(
                    children: [
                      if (_currentStep > 0)
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () =>
                                setState(() => _currentStep--),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppTheme.textSecondary,
                              side: const BorderSide(color: AppTheme.borderLight),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                              ),
                            ),
                            child: const Text('上一步'),
                          ),
                        ),
                      if (_currentStep > 0) const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _stopStepRecording,
                          icon: const Icon(Icons.stop_rounded, size: 20),
                          label: const Text('停止回答'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.error,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ] else ...[
                  Row(
                    children: [
                      if (_currentStep > 0)
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () =>
                                setState(() => _currentStep--),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: AppTheme.textSecondary,
                              side: const BorderSide(color: AppTheme.borderLight),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                              ),
                            ),
                            child: const Text('上一步'),
                          ),
                        ),
                      if (_currentStep > 0) const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: record.status == _StepRecordStatus.completed
                              ? null
                              : _startStepRecording,
                          icon: Icon(
                            _currentStep == _steps.length - 1
                                ? Icons.mic : Icons.mic,
                            size: 20,
                          ),
                          label: Text(
                            record.status == _StepRecordStatus.processing
                                ? '分析中...'
                                : _currentStep == _steps.length - 1
                                    ? '开始面试 →'
                                    : '开始回答 →'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],

                // 步骤状态汇总
                if (!_isRecording) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      for (int i = 0; i < _steps.length; i++) ...[
                        if (i > 0) const SizedBox(width: 4),
                        _buildStepDot(i),
                      ],
                      const Spacer(),
                      Text(
                        '已完成 ${_stepRecords.where((r) =>
                            r.status == _StepRecordStatus.completed).length}/${_steps.length}',
                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 24),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('面试进度',
                      style: TextStyle(fontSize: 13,
                          color: AppTheme.textSecondary)),
                  Text('${((_currentStep + 1) / _steps.length * 100).toInt()}%',
                      style: const TextStyle(fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textPrimary)),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: (_currentStep + 1) / _steps.length,
                  minHeight: 6,
                  backgroundColor: AppTheme.borderLight,
                  valueColor: const AlwaysStoppedAnimation(AppTheme.brand500),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildStepDot(int index) {
    final sr = _stepRecords[index];
    final active = index == _currentStep;
    Color color;
    if (sr.status == _StepRecordStatus.completed) {
      color = AppTheme.success;
    } else if (sr.status == _StepRecordStatus.processing) {
      color = AppTheme.warning;
    } else if (active) {
      color = AppTheme.brand500;
    } else {
      color = AppTheme.borderLight;
    }
    return Container(
      width: 8, height: 8,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
      ),
    );
  }

  // ──────────── Tab 3: 评估报告 ────────────
  Widget _buildReportTab() {
    if (_reports == null || _reports!.isEmpty) {
      return _buildDemoReportView();
    }

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      itemCount: _reports!.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final report = _reports![index];
        return _buildReportCard(index, report);
      },
    );
  }

  Widget _buildReportCard(int index, Map<String, dynamic> report) {
    final score = report['score'] as int? ?? 0;
    final grade = score >= 90 ? '卓越' : score >= 80 ? '优秀'
        : score >= 70 ? '良好' : score >= 60 ? '一般' : '待提高';
    return Container(
      decoration: AppTheme.cardDecoration,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ReportPage(data: report),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    gradient: AppTheme.gradientPrimary,
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
                      Text('面试评估 #${index + 1}',
                          style: const TextStyle(fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 4),
                      Text('$score 分 · $grade',
                          style: const TextStyle(fontSize: 13,
                              color: AppTheme.textSecondary)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right,
                    color: AppTheme.textMuted, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDemoReportView() {
    final report = ReportPage.mockData();
    final score = report['score'] as int? ?? 85;
    final grade = score >= 90 ? '卓越' : score >= 80 ? '优秀'
        : score >= 70 ? '良好' : score >= 60 ? '一般' : '待提高';
    final metrics = report['metrics'] as Map<String, int>? ?? {
      '表达清晰度': 88, '技术深度': 82, '逻辑思维': 90,
      '沟通能力': 85, '应变能力': 78, '专业知识': 80,
    };

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(
              color: AppTheme.warningBg,
              borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.auto_awesome, size: 14, color: AppTheme.warning),
                SizedBox(width: 6),
                Text('模拟报告 · 仅供参考',
                    style: TextStyle(fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: AppTheme.warning)),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('面试表现分析',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary, letterSpacing: -0.03)),
                SizedBox(height: 6),
                Text('基于 AI 多维评估模型，全面分析你的面试表现',
                    style: TextStyle(fontSize: 14,
                        color: AppTheme.textSecondary)),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(24),
            decoration: AppTheme.cardDecoration,
            child: Column(
              children: [
                Row(
                  children: [
                    Text('$score',
                        style: const TextStyle(fontSize: 56,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.brand500)),
                    const SizedBox(width: 4),
                    const Text('/100',
                        style: TextStyle(fontSize: 18,
                            fontWeight: FontWeight.w500,
                            color: AppTheme.textMuted)),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.brand50,
                        borderRadius: BorderRadius.circular(
                            AppTheme.radiusFull),
                      ),
                      child: Text(grade,
                          style: const TextStyle(fontSize: 13,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.brand500)),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                ...metrics.entries.map((e) => _buildMetricBar(e.key, e.value)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: AppTheme.cardDecoration,
            child: Column(
              children: [
                const Text('能力维度雷达图',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary)),
                const SizedBox(height: 12),
                SizedBox(
                  height: 220,
                  child: _RadarChart(
                    values: metrics.values.map((v) => v / 100).toList(),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _buildInsightCard(
                  title: '优势亮点',
                  items: const ['逻辑结构清晰，使用 STAR 法则组织回答',
                    '技术深度突出，结合真实项目经验',
                    '表达流畅自信，语速适中'],
                  tags: const ['架构思维', 'STAR 法则', '表达力'],
                  isStrength: true,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildInsightCard(
                  title: '改进建议',
                  items: const ['用数据支撑观点，展示定量分析思路',
                    '部分技术描述可更简洁，避免冗长'],
                  tags: const ['数据思维', '简洁表达'],
                  isStrength: false,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => ReportPage(data: report),
                  ),
                );
              },
              icon: const Icon(Icons.description_outlined),
              label: const Text('查看完整报告'),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildMetricBar(String label, int value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 13,
                  color: AppTheme.textSecondary)),
              Text('$value', style: const TextStyle(fontSize: 13,
                  fontWeight: FontWeight.w500, color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: value / 100,
              minHeight: 5,
              backgroundColor: AppTheme.borderLight,
              valueColor: const AlwaysStoppedAnimation(AppTheme.brand500),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInsightCard({
    required String title,
    required List<String> items,
    required List<String> tags,
    required bool isStrength,
  }) {
    final iconColor = isStrength ? AppTheme.success : AppTheme.warning;
    final iconBg = isStrength ? AppTheme.successBg : AppTheme.warningBg;
    final iconText = isStrength ? '+' : '!';
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(isStrength ? Icons.favorite : Icons.trending_up,
                  color: iconColor, size: 18),
              const SizedBox(width: 6),
              Text(title, style: const TextStyle(fontSize: 14,
                  fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          ...items.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 20, height: 20,
                  decoration: BoxDecoration(
                    color: iconBg,
                    borderRadius: BorderRadius.circular(5),
                  ),
                  child: Center(
                    child: Text(iconText, style: TextStyle(fontSize: 11,
                        fontWeight: FontWeight.w700, color: iconColor)),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(item, style: const TextStyle(fontSize: 13,
                      color: AppTheme.textSecondary, height: 1.5)),
                ),
              ],
            ),
          )),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6, runSpacing: 6,
            children: tags.map((tag) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.bgPage,
                borderRadius: BorderRadius.circular(AppTheme.radiusFull),
              ),
              child: Text(tag, style: const TextStyle(fontSize: 11,
                  fontWeight: FontWeight.w500, color: AppTheme.textSecondary)),
            )).toList(),
          ),
        ],
      ),
    );
  }
}

class _StepData {
  final String name;
  final String duration;
  final String question;
  final String tip;
  const _StepData(this.name, this.duration, this.question, this.tip);
}

// ─── Radar Chart ───
class _RadarChart extends StatelessWidget {
  final List<double> values;
  const _RadarChart({required this.values});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return CustomPaint(
          size: Size(constraints.maxWidth, constraints.maxHeight),
          painter: _RadarPainter(values),
        );
      },
    );
  }
}

class _RadarPainter extends CustomPainter {
  final List<double> values;
  _RadarPainter(this.values);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 20;
    final n = values.length;
    final angleStep = 2 * pi / n;
    final labels = ['表达清晰度', '技术深度', '逻辑思维', '沟通能力', '应变能力', '专业知识'];

    final gridPaint = Paint()
      ..color = AppTheme.borderLight
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    for (int ring = 1; ring <= 5; ring++) {
      final r = radius * ring / 5;
      final path = Path();
      for (int i = 0; i < n; i++) {
        final angle = -pi / 2 + i * angleStep;
        final x = center.dx + r * cos(angle);
        final y = center.dy + r * sin(angle);
        i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
      }
      path.close();
      canvas.drawPath(path, gridPaint);
    }

    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      canvas.drawLine(
        center,
        Offset(center.dx + radius * cos(angle),
            center.dy + radius * sin(angle)),
        gridPaint,
      );
    }

    final dataPaint = Paint()
      ..color = AppTheme.brand500.withOpacity(0.12)
      ..style = PaintingStyle.fill;
    final dataBorder = Paint()
      ..color = AppTheme.brand500
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;
    final dataPath = Path();
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      i == 0 ? dataPath.moveTo(x, y) : dataPath.lineTo(x, y);
    }
    dataPath.close();
    canvas.drawPath(dataPath, dataPaint);
    canvas.drawPath(dataPath, dataBorder);

    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final pt = Offset(center.dx + r * cos(angle),
          center.dy + r * sin(angle));
      canvas.drawCircle(pt, 5, Paint()..color = AppTheme.brand500);
      canvas.drawCircle(pt, 2.5, Paint()..color = Colors.white);
    }

    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final x = center.dx + (radius + 18) * cos(angle);
      final y = center.dy + (radius + 18) * sin(angle);
      final tp = TextPainter(
        text: TextSpan(
          text: labels[i],
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 10,
            fontWeight: FontWeight.w500,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(x - tp.width / 2, y - tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) => old.values != values;
}
