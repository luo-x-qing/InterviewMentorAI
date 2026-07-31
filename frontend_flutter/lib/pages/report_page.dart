import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend_flutter/theme.dart';
import 'package:frontend_flutter/utils/helpers.dart';
import 'package:frontend_flutter/widgets/metric_bar.dart';
import 'package:frontend_flutter/widgets/insight_card.dart';
import 'package:frontend_flutter/widgets/radar_chart.dart';

class ReportPage extends StatelessWidget {
  final Map<String, dynamic>? data;

  const ReportPage({super.key, this.data});

  static Map<String, dynamic> mockData() => {
    'score': 85,
    'metrics': {
      '表达清晰度': 88, '技术深度': 82, '逻辑思维': 90,
      '沟通能力': 85, '应变能力': 78, '专业知识': 80,
    },
    'report': mockReport,
  };

  static const mockReport = '''# 面试复盘报告

**面试岗位：** 高级前端工程师 · **面试日期：** 2026-07-30 · **面试时长：** 约 17 分钟

---

## 总体评价

本次模拟面试表现 **优秀（85/100）**。候选人在**逻辑思维**和**表达清晰度**方面表现突出，展现出扎实的技术功底和良好的沟通素养。技术能力扎实，项目经验丰富，但在**应变能力**和**技术深度的细节阐述**上仍有提升空间。整体来看，这是一次高质量的面试表现。

---

## 分步评估

### 1. 自我介绍（评分：88）

**优势：**
- 结构清晰，从教育背景→核心技能→职业动机层层递进，逻辑性强
- 重点突出 3 个与岗位最匹配的技术栈（React 生态、TypeScript、Node.js），针对性强
- 时长控制得当，约 1 分 45 秒，简洁有力

**改进建议：**
- 可增加具体数据支撑：例如"通过优化首屏加载使 FCP 降低 40%"
- 结尾可更自然过渡到对公司的了解，展现求职诚意

---

### 2. 技术能力（评分：82）

**优势：**
- STAR 法则运用得当，完整描述了从性能监控发现问题到解决方案落地的全过程
- 技术方案选型合理，Service Worker + IndexedDB 的离线缓存方案有深度
- 涉及技术栈全面（Webpack、Lighthouse、Workbox），展示全栈思维

**改进建议：**
- 量化指标不够具体："加载速度提升"最好给出精确百分比
- 可以补充遇到的技术权衡取舍，展示架构决策能力

---

### 3. 项目经验（评分：90）

**优势：**
- 架构设计思路清晰，从数据层→服务层→前端层分层阐述，覆盖面广
- 考虑到可扩展性（微前端拆分）、安全性（CSP/CSRF 防护）和团队协作（Monorepo 策略）
- 引入了具体工具链选型（Nx、Module Federation），技术视野开阔

**改进建议：**
- 可补充成本考量：SaaS 平台初期未必需要微前端，渐进式架构可能更务实
- 缺少对数据一致性方案的讨论（分布式事务 vs. 最终一致性）

---

### 4. 情景分析（评分：78）

**优势：**
- 应对策略清晰：评估影响→沟通协商→制定折中方案→风险管理
- 展现了良好的沟通意识和优先级判断能力
- 提出了具体的 trade-off 建议（先上线 MVP 核心功能，后续迭代补齐）

**改进建议：**
- 沟通话术可更具体：例如如何量化"技术风险"向产品团队表达
- 可补充实际案例经验，让回答更有说服力
- 建议预留 buffer 时间应对突发问题

---

### 5. 总结提问（评分：85）

**优势：**
- 客观地总结了自身表现，既有自信又保持了谦逊态度
- 提出的反问问题有深度："团队目前最大的技术债务是什么？""如何衡量前端团队的工作产出？"
- 展现出对团队发展和技术成长的关注

**改进建议：**
- 可准备 1-2 个关于业务方向的问题，展示商业思维
- 总结时如能引用面试中聊到的具体话题，会更有针对性

---

## 综合建议

### 短期提升（1-2 周）
1. **量化思维训练**：在描述技术成果时，养成先用数据说话的习惯
2. **场景演练**：针对情景分析类问题，提前准备 2-3 个真实的冲突解决案例
3. **反问问题库**：准备 5-8 个高质量的面试反问问题，针对不同角色（HR/技术主管/总监）分类

### 中期发展（1-3 个月）
1. **架构能力深化**：深入学习分布式系统设计、DDD 领域驱动设计
2. **技术影响力**：开始在团队内做技术分享，锻炼表达能力
3. **开源贡献**：参与 1-2 个前端开源项目，积累协作经验

### 长期规划（6-12 个月）
1. **全栈拓展**：系统学习后端技术（Node.js/Go），向全栈方向延伸
2. **技术管理**：阅读《经理人参阅》等管理书籍，为 Tech Lead 角色做准备
3. **个人品牌**：通过技术博客或演讲建立个人技术品牌

---

## 能力维度评分

| 维度 | 评分 | 评级 |
|------|------|------|
| 表达清晰度 | 88/100 | 优秀 |
| 技术深度 | 82/100 | 良好 |
| 逻辑思维 | 90/100 | 卓越 |
| 沟通能力 | 85/100 | 优秀 |
| 应变能力 | 78/100 | 良好 |
| 专业知识 | 80/100 | 良好 |

> 报告由 AI 面试助手自动生成，仅供参考。持续练习，不断进步！ 🚀
''';

  @override
  Widget build(BuildContext context) {
    final args = data ?? mockData();
    final reportContent = args['report'] as String? ?? mockReport;
    final score = args['score'] as int? ?? 85;
    final grade = AppHelpers.gradeLabel(score);
    final metrics = args['metrics'] as Map<String, int>? ?? {
      '表达清晰度': 88, '技术深度': 82, '逻辑思维': 90,
      '沟通能力': 85, '应变能力': 78, '专业知识': 80,
    };

    return Scaffold(
      backgroundColor: AppTheme.bgPage,
      appBar: AppBar(
        title: const Text('面试复盘报告'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth > 600;
          if (isWide) {
            return _buildWideLayout(
                reportContent, score, grade, metrics);
          }
          return _buildNarrowLayout(
              reportContent, score, grade, metrics);
        },
      ),
    );
  }

  Widget _buildNarrowLayout(
      String reportContent, int score, String grade,
      Map<String, int> metrics) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('评估报告',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: AppTheme.brand500)),
          const SizedBox(height: 8),
          const Text('面试表现分析',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          const Text('基于 AI 多维评估模型，全面分析你的面试表现',
              style: TextStyle(fontSize: 14,
                  color: AppTheme.textSecondary)),
          const SizedBox(height: 24),
          _buildScoreCard(score, grade, metrics),
          const SizedBox(height: 16),
          _buildRadarCard(metrics),
          const SizedBox(height: 16),
          _buildInsightRow(),
          if (reportContent.isNotEmpty &&
              reportContent != '暂无分析内容') ...[
            const SizedBox(height: 24),
            const Text('详细分析报告',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: AppTheme.cardDecoration,
              child: MarkdownBody(
                data: reportContent,
                styleSheet: MarkdownStyleSheet(
                  h1: const TextStyle(fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary),
                  h2: const TextStyle(fontSize: 17,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary),
                  p: const TextStyle(fontSize: 14,
                      color: AppTheme.textSecondary, height: 1.6),
                ),
              ),
            ),
          ],
          const SizedBox(height: 28),
        ],
      ),
    );
  }

  Widget _buildWideLayout(
      String reportContent, int score, String grade,
      Map<String, int> metrics) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('评估报告',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                  letterSpacing: 1.2, color: AppTheme.brand500)),
          const SizedBox(height: 8),
          const Text('面试表现分析',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          const Text('基于 AI 多维评估模型，全面分析你的面试表现',
              style: TextStyle(fontSize: 14,
                  color: AppTheme.textSecondary)),
          const SizedBox(height: 24),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 3, child: _buildRadarCard(metrics)),
              const SizedBox(width: 20),
              Expanded(
                flex: 4,
                child: Column(
                  children: [
                    _buildScoreCard(score, grade, metrics),
                    const SizedBox(height: 16),
                    _buildInsightRow(),
                  ],
                ),
              ),
            ],
          ),
          if (reportContent.isNotEmpty &&
              reportContent != '暂无分析内容') ...[
            const SizedBox(height: 28),
            const Text('详细分析报告',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: AppTheme.cardDecoration,
              child: MarkdownBody(
                data: reportContent,
                styleSheet: MarkdownStyleSheet(
                  h1: const TextStyle(fontSize: 20,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary),
                  h2: const TextStyle(fontSize: 17,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary),
                  p: const TextStyle(fontSize: 14,
                      color: AppTheme.textSecondary, height: 1.6),
                ),
              ),
            ),
          ],
          const SizedBox(height: 28),
        ],
      ),
    );
  }

  Widget _buildScoreCard(int score, String grade,
      Map<String, int> metrics) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: AppTheme.cardDecoration,
      child: Column(
        children: [
          Row(
            children: [
              Text('$score',
                  style: const TextStyle(fontSize: 56,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.brand500, height: 1)),
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
          ...metrics.entries
              .map((e) => MetricBar(label: e.key, value: e.value)),
        ],
      ),
    );
  }

  Widget _buildRadarCard(Map<String, int> metrics) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.cardDecoration,
      child: Column(
        children: [
          const Text('能力维度雷达图',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 12),
          SizedBox(
            height: 260,
            child: RadarChart(
              values: metrics.values.map((v) => v / 100).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInsightRow() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: InsightCard(
            title: '优势亮点',
            items: const ['逻辑结构清晰，使用 STAR 法则组织回答',
             '技术深度突出，结合真实项目经验',
             '表达流畅自信，语速适中'],
            isStrength: true,
            tags: const ['架构思维', 'STAR 法则', '表达力'],
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: InsightCard(
            title: '改进建议',
            items: const ['用数据支撑观点，展示定量分析思路',
             '部分技术描述可更简洁，避免冗长'],
            isStrength: false,
            tags: const ['数据思维', '简洁表达'],
          ),
        ),
      ],
    );
  }
}
