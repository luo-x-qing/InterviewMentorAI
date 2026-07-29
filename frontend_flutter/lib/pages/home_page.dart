import 'package:flutter/material.dart';
import 'package:frontend_flutter/theme.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentStep = 0;
  int _navIndex = 1;

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

  void _setStep(int index) {
    setState(() => _currentStep = index.clamp(0, _steps.length - 1));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildNav(),
            Expanded(child: _buildPage()),
          ],
        ),
      ),
    );
  }

  Widget _buildNav() {
    final items = ['录音', '面试流程', '评估报告'];
    return Container(
      margin: const EdgeInsets.fromLTRB(20, 12, 20, 4),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppTheme.radiusFull),
        border: Border.all(color: AppTheme.borderLight),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0D000000), blurRadius: 8, offset: Offset(0, 2)),
        ],
      ),
      child: Row(
        children: List.generate(items.length, (i) {
          final active = _navIndex == i;
          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _navIndex = i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  gradient: active
                      ? const LinearGradient(colors: [AppTheme.gradientStart, AppTheme.gradientEnd])
                      : null,
                  borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                ),
                child: Text(
                  items[i],
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: active ? Colors.white : AppTheme.textSecondary,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildPage() {
    switch (_navIndex) {
      case 0: return _buildRecordTab();
      case 1: return _buildInterviewTab();
      case 2: return _buildReportTab();
      default: return const SizedBox();
    }
  }

  // ──────────── Tab 1: 录音 ────────────
  Widget _buildRecordTab() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Spacer(flex: 2),
          const Text('AI 面试助手',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: AppTheme.brand500)),
          const SizedBox(height: 12),
          const Text('开始你的模拟面试',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 40),
            child: Text('点击下方按钮开始录音，AI 将实时分析你的回答并生成专业评估报告',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15, color: AppTheme.textSecondary)),
          ),
          const Spacer(flex: 2),
          GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/record'),
            child: Container(
              width: 144, height: 144,
              decoration: AppTheme.glowDecoration,
              child: const Icon(Icons.mic_rounded, size: 54, color: Colors.white),
            ),
          ),
          const Spacer(flex: 3),
        ],
      ),
    );
  }

  // ──────────── Tab 2: 面试流程 ────────────
  Widget _buildInterviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          const Text('分步引导 · 精准评估',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          const Text('从自我介绍到情景分析，AI 引导你完成完整的面试模拟',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          const SizedBox(height: 28),

          // Timeline + Content
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Left timeline
              SizedBox(
                width: 160,
                child: Column(
                  children: List.generate(_steps.length, (i) {
                    final active = _currentStep == i;
                    final done = i < _currentStep;
                    return GestureDetector(
                      onTap: () => _setStep(i),
                      child: Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: active
                              ? AppTheme.brand50
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                          border: active
                              ? Border.all(color: AppTheme.brand100)
                              : null,
                        ),
                        child: Row(
                          children: [
                            _buildStepNum(i + 1, done, active),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(_steps[i].name,
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w500,
                                        color: active
                                            ? AppTheme.textPrimary
                                            : AppTheme.textSecondary,
                                      )),
                                  Text(_steps[i].duration,
                                      style: const TextStyle(
                                          fontSize: 11, color: AppTheme.textMuted)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ),
              const SizedBox(width: 16),

              // Right content card
              Expanded(
                child: Container(
                  constraints: const BoxConstraints(minHeight: 380),
                  padding: const EdgeInsets.all(28),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_steps[_currentStep].name,
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.brand50,
                          borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                        ),
                        child: Text(
                          '步骤 ${_currentStep + 1}/${_steps.length}',
                          style: const TextStyle(
                              fontSize: 12, fontWeight: FontWeight.w500,
                              color: AppTheme.brand500),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: AppTheme.bgPage,
                          borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                          border: const Border(
                            left: BorderSide(color: AppTheme.brand500, width: 3),
                          ),
                        ),
                        child: Text(_steps[_currentStep].question,
                            style: const TextStyle(
                                fontSize: 15, color: AppTheme.textSecondary,
                                height: 1.7)),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          const Icon(Icons.lightbulb_outline,
                              size: 16, color: AppTheme.textMuted),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text('提示：${_steps[_currentStep].tip}',
                                style: const TextStyle(
                                    fontSize: 13, color: AppTheme.textMuted)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      Row(
                        children: [
                          if (_currentStep > 0)
                            _buildButton('← 上一步', false, () => _setStep(_currentStep - 1)),
                          if (_currentStep > 0) const SizedBox(width: 12),
                          _buildButton(
                            _currentStep < _steps.length - 1 ? '开始回答 →' : '完成面试 · 查看报告 →',
                            true,
                            () {
                              if (_currentStep < _steps.length - 1) {
                                _setStep(_currentStep + 1);
                              } else {
                                setState(() => _navIndex = 2);
                              }
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const Divider(),
          const SizedBox(height: 32),

          // Progress bar
          Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('面试进度',
                      style: TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                  Text('${((_currentStep + 1) / _steps.length * 100).round()}%',
                      style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: (_currentStep + 1) / _steps.length,
                  minHeight: 6,
                  backgroundColor: AppTheme.borderLight,
                  valueColor: const AlwaysStoppedAnimation(AppTheme.gradientStart),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStepNum(int num, bool done, bool active) {
    return Container(
      width: 32, height: 32,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: done
            ? AppTheme.brand500
            : active
                ? AppTheme.brand50
                : AppTheme.bgCard,
        border: Border.all(
          color: done ? Colors.transparent : AppTheme.borderLight,
          width: 2,
        ),
        boxShadow: done
            ? const [BoxShadow(color: Color(0x334F46E5), blurRadius: 8, offset: Offset(0, 2))]
            : null,
      ),
      child: done
          ? const Icon(Icons.check, size: 16, color: Colors.white)
          : Center(
              child: Text('$num',
                  style: TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600,
                    color: active ? AppTheme.brand500 : AppTheme.textMuted,
                  )),
            ),
    );
  }

  Widget _buildButton(String text, bool primary, VoidCallback onTap) {
    if (primary) {
      return GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.gradientStart, AppTheme.gradientEnd]),
            borderRadius: BorderRadius.circular(AppTheme.radiusFull),
            boxShadow: const [
              BoxShadow(color: Color(0x334F46E5), blurRadius: 12, offset: Offset(0, 4)),
            ],
          ),
          child: Text(text,
              style: const TextStyle(
                  color: Colors.white, fontWeight: FontWeight.w500, fontSize: 14)),
        ),
      );
    }
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: AppTheme.textSecondary,
        side: const BorderSide(color: AppTheme.borderLight),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTheme.radiusFull),
        ),
      ),
      child: Text(text, style: const TextStyle(fontSize: 14)),
    );
  }

  // ──────────── Tab 3: 报告预览 ────────────
  Widget _buildReportTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          const Text('评估报告',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: AppTheme.brand500)),
          const SizedBox(height: 8),
          const Text('面试表现分析',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          const Text('基于 AI 多维评估模型，全面分析你的面试表现',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          const SizedBox(height: 28),

          // Score overview
          Row(
            children: [
              // Radar placeholder
              Expanded(
                flex: 3,
                child: Container(
                  padding: const EdgeInsets.all(24),
                  decoration: AppTheme.cardDecoration,
                  child: Column(
                    children: [
                      const Text('能力维度雷达图',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary)),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 260,
                        child: _RadarChart(values: [0.88, 0.82, 0.90, 0.85, 0.78, 0.86]),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 20),
              // Score card
              Expanded(
                flex: 4,
                child: Column(
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(28),
                      decoration: AppTheme.cardDecoration,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              const Text('85',
                                  style: TextStyle(fontSize: 56, fontWeight: FontWeight.w600,
                                      color: AppTheme.brand500, height: 1)),
                              const Text(' /100',
                                  style: TextStyle(fontSize: 16, color: AppTheme.textMuted)),
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppTheme.brand50,
                                  borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                                ),
                                child: const Text('优秀',
                                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
                                        color: AppTheme.brand500)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),
                          _buildMetricBar('表达清晰度', 88),
                          _buildMetricBar('技术深度', 82),
                          _buildMetricBar('逻辑思维', 90),
                          _buildMetricBar('沟通能力', 85),
                          _buildMetricBar('应变能力', 78),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Strengths + Improvements
                    Row(
                      children: [
                        Expanded(child: _buildInsightCard(
                          '💪 优势亮点',
                          ['逻辑结构清晰，使用 STAR 法则组织回答',
                           '技术深度突出，结合真实项目经验',
                           '表达流畅自信，语速适中'],
                          isStrength: true,
                        )),
                        const SizedBox(width: 16),
                        Expanded(child: _buildInsightCard(
                          '🎯 改进建议',
                          ['用数据支撑观点，展示定量分析',
                           '部分技术描述可更简洁'],
                          isStrength: false,
                        )),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 28),
          const Divider(),
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
              Text(label, style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
              Text('$value', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500,
                  color: AppTheme.textPrimary)),
            ],
          ),
          const SizedBox(height: 5),
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

  Widget _buildInsightCard(String title, List<String> items,
      {required bool isStrength}) {
    final iconColor = isStrength ? AppTheme.success : AppTheme.warning;
    final iconBg = isStrength ? AppTheme.successBg : AppTheme.warningBg;
    final iconText = isStrength ? '+' : '!';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 14),
          ...items.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 22, height: 22,
                  decoration: BoxDecoration(
                    color: iconBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Center(
                    child: Text(iconText,
                        style: TextStyle(
                            fontSize: 12, fontWeight: FontWeight.w600,
                            color: iconColor)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(item,
                      style: const TextStyle(
                          fontSize: 13, color: AppTheme.textSecondary, height: 1.5)),
                ),
              ],
            ),
          )),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: (isStrength
                    ? ['架构思维', 'STAR 法则', '表达力']
                    : ['数据思维', '简洁表达']
                ).map((tag) => Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.bgPage,
                    borderRadius: BorderRadius.circular(AppTheme.radiusFull),
                  ),
                  child: Text(tag,
                      style: const TextStyle(
                          fontSize: 11, fontWeight: FontWeight.w500,
                          color: AppTheme.textSecondary)),
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

// ─── Simple Radar Chart ───
class _RadarChart extends StatelessWidget {
  final List<double> values;
  const _RadarChart({required this.values});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size.fromHeight(260),
      painter: _RadarPainter(values),
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

    // Grid
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
        if (i == 0) path.moveTo(x, y);
        else path.lineTo(x, y);
      }
      path.close();
      canvas.drawPath(path, gridPaint);
    }

    // Axis lines
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final x = center.dx + radius * cos(angle);
      final y = center.dy + radius * sin(angle);
      canvas.drawLine(center, Offset(x, y), gridPaint);
    }

    // Data area
    final dataPaint = Paint()
      ..color = AppTheme.brand500.withValues(alpha: 0.15)
      ..style = PaintingStyle.fill;
    final dataBorder = Paint()
      ..color = AppTheme.brand500
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    final dataPath = Path();
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      if (i == 0) dataPath.moveTo(x, y);
      else dataPath.lineTo(x, y);
    }
    dataPath.close();
    canvas.drawPath(dataPath, dataPaint);
    canvas.drawPath(dataPath, dataBorder);

    // Data points
    final dotPaint = Paint()
      ..color = AppTheme.brand500
      ..style = PaintingStyle.fill;
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final r = radius * values[i].clamp(0.0, 1.0);
      final x = center.dx + r * cos(angle);
      final y = center.dy + r * sin(angle);
      canvas.drawCircle(Offset(x, y), 4, dotPaint);
      canvas.drawCircle(Offset(x, y), 2.5, Paint()..color = Colors.white..style = PaintingStyle.fill);
    }

    // Labels
    for (int i = 0; i < n; i++) {
      final angle = -pi / 2 + i * angleStep;
      final x = center.dx + (radius + 18) * cos(angle);
      final y = center.dy + (radius + 18) * sin(angle);
      final tp = TextPainter(
        text: TextSpan(
          text: labels[i],
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 11,
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
