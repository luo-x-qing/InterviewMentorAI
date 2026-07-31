import 'package:frontend_flutter/models/post.dart';

/// 20+ 社区帖子 mock 数据
final List<PostModel> mockPosts = [
  PostModel(
    id: 'p01', authorName: '前端小王', title: '从零到Offer：我的三个月前端进阶之路',
    content: '''## 背景
我是一名转行前端的新人，去年 10 月开始系统学习前端，今年 1 月拿到了满意的 Offer。分享一下我的学习路径。

## 学习路径
1. **基础阶段（1 个月）**：HTML + CSS + JavaScript 基础，重点攻克了闭包、原型链、事件循环
2. **框架阶段（1 个月）**：React 生态（Hooks + Router + Redux），跟着官方文档做了 3 个实战项目
3. **面试冲刺（1 个月）**：LeetCode 刷了 80 题，模拟面试 10+ 次，用 InterviewMentorAI 做了 5 次复盘

## 关键心得
- 不要只学不用，每个知识点都要写代码验证
- 面试复盘比多刷 10 道题更有价值
- 保持自信，技术面考察的是思维过程而非标准答案''',
    tags: ['面经分享'], likeCount: 23, commentCount: 5,
    createdAt: DateTime.now().subtract(const Duration(days: 3)),
    comments: [
      CommentModel(id: 'c01', postId: 'p01', authorName: '李明', content: '太有用了！我和你背景很像，给了我很大信心。', createdAt: DateTime.now().subtract(const Duration(days: 2))),
      CommentModel(id: 'c02', postId: 'p01', authorName: '前端小王', content: '谢谢！一起加油 💪', createdAt: DateTime.now().subtract(const Duration(days: 2))),
    ],
  ),
  PostModel(
    id: 'p02', authorName: '资深面试官', title: '大厂面试官视角：我们到底在考察什么',
    content: '''面试了 5 年，面过 500+ 候选人，分享一些面试官的真实想法。

## 我们不是在找"标准答案"
很多候选人背诵八股文，但面试真正考察的是：
1. **思维过程**：你是如何分析问题的？遇到不熟悉的问题能否合理推理？
2. **技术深度**：不是你会用这个 API，而是你理解它为什么这样设计
3. **沟通能力**：能否清晰地表达复杂技术概念？遇到分歧如何沟通？

## STAR 法则真的重要
行为问题请一定用 STAR 法则结构化回答。空洞的"我沟通能力很强"不如一个具体的冲突解决故事。

## 给候选人的建议
- 准备 2-3 个你真正理解深入的技术话题（你的"技术杀手锏"）
- 面试最后一定要问问题（展现你的好奇心）
- 不要过分谦虚，也不要夸大其词''',
    tags: ['面经分享'], likeCount: 56, commentCount: 8,
    createdAt: DateTime.now().subtract(const Duration(days: 5)),
    comments: [
      CommentModel(id: 'c03', postId: 'p02', authorName: '求职者A', content: '面试官视角太珍贵了，收藏！', createdAt: DateTime.now().subtract(const Duration(days: 4))),
      CommentModel(id: 'c04', postId: 'p02', authorName: '小刘', content: '请问STAR法则具体怎么用？有没有好的例子？', createdAt: DateTime.now().subtract(const Duration(days: 3))),
    ],
  ),
  PostModel(
    id: 'p03', authorName: '全栈工程师', title: '前端高频面试题总结（2026最新版）',
    content: '''整理了今年面试中被问频率最高的 20 道题：

1. 闭包原理及应用
2. 事件循环（宏任务/微任务）
3. 虚拟 DOM 和 Diff 算法
4. React Hooks 使用规则
5. 浏览器缓存策略
6. HTTP/2 和 HTTP/3
7. Webpack vs Vite
8. TypeScript 高级类型
9. 性能优化实战
10. 微前端架构

每道题我都写了详细解答，需要的可以私聊交流！''',
    tags: ['技术讨论'], likeCount: 89, commentCount: 12,
    createdAt: DateTime.now().subtract(const Duration(days: 7)),
    comments: [
      CommentModel(id: 'c05', postId: 'p03', authorName: '前端萌新', content: '太及时了！明天面试刚好用上。', createdAt: DateTime.now().subtract(const Duration(days: 6))),
    ],
  ),
  PostModel(
    id: 'p04', authorName: '设计师转前端', title: '非科班出身如何让面试官眼前一亮？',
    content: '''我是设计转前端的，刚开始面试时总被质疑"基础不扎实"。

## 我的破局策略
1. **利用设计背景作为优势**：面试中强调我对 UI/UX 的理解，能在前端还原设计稿时主动提出更好的交互方案
2. **开源项目证明能力**：花了 2 个月做了一个 React 组件库，开源在 GitHub 上，面试时直接展示
3. **量化成果**：不说"我学习能力强"，而是说"我自学 3 个月完成了一个有 50+ star 的开源项目"

**建议**：非科班不要试图掩盖背景，而是把它变成你的独特优势。''',
    tags: ['求职互助'], likeCount: 34, commentCount: 7,
    createdAt: DateTime.now().subtract(const Duration(days: 10)),
  ),
  PostModel(
    id: 'p05', authorName: 'React 爱好者', title: 'React 19 新特性：use() Hook 深入解析',
    content: '''React 19 引入了全新的 `use()` Hook，可以直接在组件中使用 Promise 和 Context。

```javascript
// 之前
const data = useContext(MyContext);

// 之后（支持 Promise）
const data = use(fetchData());  // 自动触发 Suspense
```

**关键特性**：条件调用、自动 Suspense 集成、与 Context 原生兼容。

你们开始用 React 19 了吗？对这个新 Hook 有什么看法？''',
    tags: ['技术讨论'], likeCount: 45, commentCount: 15,
    createdAt: DateTime.now().subtract(const Duration(days: 2)),
    comments: [
      CommentModel(id: 'c06', postId: 'p05', authorName: 'Vue用户', content: 'Vue 早就有了类似的 await setup，React 终于跟上了', createdAt: DateTime.now().subtract(const Duration(days: 1))),
      CommentModel(id: 'c07', postId: 'p05', authorName: 'React 爱好者', content: '哈哈，各有优劣吧。React 的 Suspense 架构更优雅', createdAt: DateTime.now().subtract(const Duration(days: 1, hours: 2))),
    ],
  ),
  PostModel(
    id: 'p06', authorName: '算法练习生', title: '前端需要刷多少算法题才够？',
    content: '''我的结论是：**80 题，重点在理解而不是数量**。

## 必刷分类
- 数组/字符串（15 题）：双指针、滑动窗口、哈希表
- 链表（10 题）：快慢指针、反转、合并
- 二叉树（15 题）：DFS、BFS、遍历
- 动态规划（15 题）：爬楼梯、背包、最长子序列
- 排序/搜索（10 题）：快排、二分、堆
- 设计题（5 题）：LRU、Promise.all、节流防抖

## 前端算法面试的真实难度
说实话，比后端低不少。LeetCode 中等难度就足够了，主要是考察逻辑思维而不是数学功底。''',
    tags: ['技术讨论'], likeCount: 67, commentCount: 20,
    createdAt: DateTime.now().subtract(const Duration(days: 8)),
  ),
  PostModel(
    id: 'p07', authorName: 'CS学生', title: '求助：明天面试，有什么临时抱佛脚的建议？',
    content: '''明天下午有一个前端实习面试，之前准备不够充分，求紧急建议！

已经做了：
- 整理了自我介绍
- 复习了 JS 基础（闭包、原型链、this）
- 看了 10 道常见面试题

还有什么可以今晚快速补的？焦虑中...''',
    tags: ['求职互助'], likeCount: 12, commentCount: 9,
    createdAt: DateTime.now().subtract(const Duration(hours: 8)),
    comments: [
      CommentModel(id: 'c08', postId: 'p07', authorName: '过来人', content: '别慌！今晚重点看这个公司的面经，了解他们常用的技术栈。然后好好睡一觉，精神状态比多背10道题重要！', createdAt: DateTime.now().subtract(const Duration(hours: 5))),
    ],
  ),
  PostModel(
    id: 'p08', authorName: 'TechLead张', title: '如何做好技术面试中的系统设计题',
    content: '''很多前端候选人在系统设计题上表现不佳，分享一下我的框架：

## 4 步法
1. **需求澄清**（5 分钟）：问清楚功能范围、用户量级、性能要求
2. **高层设计**（10 分钟）：画出系统架构图，模块划分
3. **深入细节**（10 分钟）：挑 2-3 个核心模块具体展开
4. **总结权衡**（5 分钟）：回顾设计中的 trade-off

**前端常见系统设计题**：
- 设计一个聊天应用前端
- 设计一个仪表盘系统
- 设计一个富文本编辑器
- 设计一个前端监控平台''',
    tags: ['面经分享', '技术讨论'], likeCount: 78, commentCount: 11,
    createdAt: DateTime.now().subtract(const Duration(days: 12)),
    linkedReportSummary: {'score': 85, 'grade': '优秀'},
    comments: [
      CommentModel(id: 'c09', postId: 'p08', authorName: '前端萌新', content: '太详细了！请问有推荐的系统设计学习资源吗？', createdAt: DateTime.now().subtract(const Duration(days: 10))),
    ],
  ),
  PostModel(
    id: 'p09', authorName: '远程打工人', title: '远程面试 vs 线下面试：优劣势对比',
    content: '''经历了 10+ 远程面试和 5 次线下面试，分享一下感受：

**远程面试优势**：
- 不用通勤，节省精力
- 可以在熟悉的环境里，更放松
- 方便展示代码和屏幕共享

**远程面试劣势**：
- 网络问题（一定要有线网络！）
- 缺少非语言交流（面试官的表情和肢体语言）
- 容易被周围环境干扰

**我的建议**：远程面试前 30 分钟把环境搭好，开启勿扰模式，用有线网络。''',
    tags: ['求职互助'], likeCount: 28, commentCount: 6,
    createdAt: DateTime.now().subtract(const Duration(days: 15)),
  ),
  PostModel(
    id: 'p10', authorName: 'Webpack 信徒', title: 'Vite vs Webpack：2026 年我们应该选哪个？',
    content: '''**开发体验**：Vite 完胜。ESM 原生支持 + 按需编译，冷启动几乎瞬间。
**生产构建**：两者差距缩小。Vite 底层用 Rollup，Webpack 5 也在追赶。
**生态成熟度**：Webpack 仍然领先，但 Vite 社区增长迅速。
**大型项目**：Webpack 的插件生态和配置灵活性在复杂场景下更具优势。

**结论**：新项目优先选 Vite，遗留 Webpack 项目不必急着迁移。''',
    tags: ['技术讨论'], likeCount: 52, commentCount: 18,
    createdAt: DateTime.now().subtract(const Duration(days: 4)),
    comments: [
      CommentModel(id: 'c10', postId: 'p10', authorName: 'Turbopack粉丝', content: 'Turbopack 不考虑吗？据说比 Vite 还快', createdAt: DateTime.now().subtract(const Duration(days: 3))),
    ],
  ),
  PostModel(
    id: 'p11', authorName: '后端转前端', title: '后端转前端半年，分享一下我的困惑和成长',
    content: '''从 Java 后端转到 React 前端已经半年了，最大的感受是前端"杂"得多。

**需要同时掌握**：JS/TS、CSS、浏览器原理、构建工具、性能优化、跨端适配...

**当然也有优势**：
- 后端思维在系统设计题上很有帮助
- 数据处理和分析能力天然强
- 全栈视角让架构设计更全面

想听听大家的转型经历！''',
    tags: ['求职互助'], likeCount: 19, commentCount: 14,
    createdAt: DateTime.now().subtract(const Duration(days: 6)),
  ),
  PostModel(
    id: 'p12', authorName: '面试经验侠', title: '那些年我在面试中踩过的坑（附避坑指南）',
    content: '''1. **简历过度包装**：写"精通 React"结果被问到原理答不上来。→ 改成"熟练掌握 React，了解核心原理"
2. **背题痕迹太重**：面试官一眼能看出你在背书。→ 用自己的话复述，加入项目中的实际例子
3. **负面评价前公司**：大忌。→ 客观描述离职原因，专注于未来成长
4. **不问问题**：显得没有好奇心。→ 准备 3-5 个有深度的问题''',
    tags: ['面经分享'], likeCount: 41, commentCount: 6,
    createdAt: DateTime.now().subtract(const Duration(days: 9)),
  ),
];
