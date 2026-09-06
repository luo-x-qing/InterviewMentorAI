import 'dart:async';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/pages/record_page.dart';
import 'package:frontend_flutter/pages/report_page.dart';
import 'package:frontend_flutter/services/audio_service.dart';
import 'package:frontend_flutter/services/api_service.dart';
import 'package:frontend_flutter/utils/helpers.dart';
import 'package:frontend_flutter/widgets/empty_state.dart';

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
  bool _reportLoading = true;
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
    _loadReports();
  }

  @override
  void dispose() {
    _recordTimer?.cancel();
    _waveformTimer?.cancel();
    AudioService.dispose();
    _tabController.dispose();
    super.dispose();
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
      if (mounted) {
        setState(() {
          _stepRecords[step].reportData = result;
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

  // ──── 报告数据 ────

  Future<void> _loadReports() async {
    try {
      final list = await ApiService.getReportList();
      if (mounted) {
        setState(() {
          _reports = list;
          _reportLoading = false;
        });
        return;
      }
    } catch (_) {
      // 网络失败时保留本地已有的报告
    }
    if (mounted) setState(() => _reportLoading = false);
  }

  // ──── 录音回调 ────

  void _onRecordingComplete(Map<String, dynamic> reportData) {
    if (reportData.isNotEmpty) {
      setState(() => (_reports ??= []).insert(0, reportData));
    }
    _showReportReadyDialog();
    // 后台静默刷新服务端列表
    _loadReports();
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
                    color: active ? AppTheme.brand500 : Colors.transparent,
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
    final report = _reports!.last;
    final title = report['title'] as String? ?? '面试复盘报告';
    final createdAt = report['created_at'] as String? ?? '';
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
                Text(title,
                    style: const TextStyle(fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                Text(createdAt.isEmpty ? '点击查看详细评估' : '$createdAt · 查看评估',
                    style: const TextStyle(fontSize: 12,
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
              separatorBuilder: (_, _) => const SizedBox(width: 6),
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
                        Text(AppHelpers.formatTime(_recordSeconds),
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
    // 加载中
    if (_reportLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppTheme.brand500),
      );
    }

    // 无报告：引导状态 + 示例入口
    if (_reports == null || _reports!.isEmpty) {
      return _buildEmptyReportGuide();
    }

    // 有报告：下拉刷新列表
    return RefreshIndicator(
      onRefresh: _loadReports,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: _reports!.length + 1, // +1 给底部示例入口
        separatorBuilder: (context, index) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          if (index < _reports!.length) {
            return _buildReportCard(index, _reports![index]);
          }
          return _buildDemoEntry();
        },
      ),
    );
  }

  /// 报告为空时的引导状态
  Widget _buildEmptyReportGuide() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          EmptyStateWidget(
            icon: Icons.assignment_outlined,
            title: '暂无面试报告',
            subtitle: '完成一次模拟面试后，AI 分析报告将显示在这里',
            action: ElevatedButton.icon(
              onPressed: () => _tabController.animateTo(0),
              icon: const Icon(Icons.mic, size: 18),
              label: const Text('开始模拟面试'),
            ),
          ),
          const SizedBox(height: 20),
          _buildDemoEntry(),
        ],
      ),
    );
  }

  /// 底部"查看示例报告"入口卡片
  Widget _buildDemoEntry() {
    return GestureDetector(
      onTap: () {
        Navigator.push(context,
            MaterialPageRoute(builder: (_) => ReportPage(data: ReportPage.mockData())));
      },
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.warningBg.withValues(alpha: 0.4),
          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
          border: Border.all(color: AppTheme.warningBg),
        ),
        child: Row(
          children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                color: AppTheme.warningBg,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.auto_awesome, color: AppTheme.warning, size: 20),
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('示例报告', style: TextStyle(fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary, fontSize: 14)),
                  Text('查看一份完整的评估报告，了解 AI 分析能力',
                      style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppTheme.textMuted, size: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildReportCard(int index, Map<String, dynamic> report) {
    final title = report['title'] as String? ?? '面试评估';
    final createdAt = report['created_at'] as String? ?? '';
    final score = report['score'] as int?;
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
                    color: AppTheme.brand50,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Center(
                    child: Text('${index + 1}',
                        style: const TextStyle(color: AppTheme.brand500,
                            fontWeight: FontWeight.w600, fontSize: 18)),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title,
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 4),
                      Text(score != null
                          ? '$score 分 · ${AppHelpers.gradeLabel(score)}'
                          : createdAt.isEmpty ? '查看详细评估' : createdAt,
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

}

class _StepData {
  final String name;
  final String duration;
  final String question;
  final String tip;
  const _StepData(this.name, this.duration, this.question, this.tip);
}
