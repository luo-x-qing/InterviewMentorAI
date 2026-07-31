import 'package:frontend_flutter/models/question.dart';

/// 60+ 道模拟面试题，6 个分类 × 10 题
final List<InterviewQuestion> mockQuestions = [
  // ──── HTML/CSS (10 题) ────
  InterviewQuestion(
    id: 'html-01', category: 'HTML/CSS', difficulty: '初级',
    title: '请解释 CSS 盒模型，并说明 box-sizing 属性的作用',
    answer: '''CSS 盒模型定义了元素在页面上所占空间的计算方式，由四个部分组成（从内到外）：
1. **内容区域（content）**：元素的实际内容，`width` 和 `height` 默认只作用于这一层
2. **内边距（padding）**：内容与边框之间的空白区域
3. **边框（border）**：包裹内容和内边距的边框
4. **外边距（margin）**：元素与其他元素之间的空白

**box-sizing 属性**：
- `content-box`（默认）：`width/height` 仅作用于内容区域，实际元素宽度 = width + padding + border
- `border-box`：`width/height` 包含 content + padding + border，布局控制更直观

**最佳实践**：项目中通常全局设置 `*, *::before, *::after { box-sizing: border-box; }`，避免尺寸计算混乱。''',
    intent: '考察对 CSS 基础概念的掌握程度，以及是否具备工程化思维（box-sizing 的最佳实践）',
    tags: ['CSS基础', '盒模型', 'box-sizing'],
  ),
  InterviewQuestion(
    id: 'html-02', category: 'HTML/CSS', difficulty: '初级',
    title: '什么是 BFC（块级格式化上下文）？如何触发？有哪些应用场景？',
    answer: '''**BFC（Block Formatting Context）** 是 CSS 布局中的一个独立渲染区域，内部元素的布局不会影响外部元素。

**触发方式**：
- `overflow` 不为 `visible`（如 `hidden`、`auto`、`scroll`）
- `display: flow-root`（最干净的触发方式）
- `float` 不为 `none`
- `position: absolute` 或 `fixed`
- `display: flex` / `grid` / `inline-block` / `table-cell`

**核心应用场景**：
1. **清除浮动**：父容器触发 BFC 后可以包裹浮动子元素（替代 clearfix）
2. **防止外边距合并**：相邻元素的 margin 在 BFC 中不会合并
3. **自适应两栏布局**：左侧固定宽度浮动，右侧触发 BFC 自适应剩余空间''',
    intent: '考察 CSS 布局机制的深入理解，BFC 是面试高频考点',
    tags: ['CSS布局', 'BFC', '浮动'],
  ),
  InterviewQuestion(
    id: 'html-03', category: 'HTML/CSS', difficulty: '中级',
    title: 'Flexbox 和 Grid 布局分别适用于什么场景？请对比它们的差异',
    answer: '''| 维度 | Flexbox | Grid |
|------|---------|------|
| 布局方向 | 一维（主轴 + 交叉轴） | 二维（行 + 列） |
| 适用场景 | 导航栏、工具栏、卡片内元素排列 | 页面整体布局、仪表盘、画廊 |
| 对齐控制 | justify-content / align-items | 额外支持 justify-items / align-content / gap |
| 响应式 | 通过 flex-wrap 换行 | 通过 fr 单位 + auto-fit/auto-fill + minmax 自适应 |

**选择原则**：
- 仅需控制一个方向的排列 → Flexbox
- 需要同时控制行与列的对齐 → Grid
- 两者可以嵌套使用，Grid 外层，Flexbox 内层是最佳实践''',
    intent: '考察现代 CSS 布局方案的选型能力和实际项目经验',
    tags: ['Flexbox', 'Grid', 'CSS布局'],
  ),
  InterviewQuestion(
    id: 'html-04', category: 'HTML/CSS', difficulty: '初级',
    title: 'CSS 选择器优先级是如何计算的？',
    answer: '''CSS 优先级（Specificity）按以下规则计算（权重递减）：
1. **!important**：最高优先级，覆盖所有（不推荐滥用）
2. **内联样式**（style 属性）：权重 1000
3. **ID 选择器**（#id）：权重 100
4. **类/属性/伪类选择器**（.class, [attr], :hover）：权重 10
5. **元素/伪元素选择器**（div, ::before）：权重 1

**注意**：
- 权重值不会进位（11 个 class 不等于 1 个 ID）
- 同等权重下，后定义的规则覆盖先定义的
- `:where()` 选择器权重始终为 0，适合做基础样式重置''',
    intent: 'CSS 基础知识，考察选择器权重的精确理解',
    tags: ['CSS基础', '选择器', '优先级'],
  ),
  InterviewQuestion(
    id: 'html-05', category: 'HTML/CSS', difficulty: '中级',
    title: '请解释浏览器的重绘（Repaint）和回流（Reflow），如何优化？',
    answer: '''**回流（Reflow）**：布局几何属性变化（宽高、位置、display 等），浏览器需要重新计算元素位置和大小。回流代价高，且会触发周边元素连锁回流。

**重绘（Repaint）**：仅外观样式变化（颜色、背景、阴影等），不影响几何属性。重绘代价相对较低。

**优化策略**：
1. **批量修改 DOM**：使用 `documentFragment` 或 `display: none` 脱离文档流后修改
2. **避免逐条修改样式**：使用 `classList` 切换类名替代直接修改 style
3. **脱离文档流**：动画元素使用 `position: absolute/fixed` 或 `transform`
4. **使用 CSS 动画**：`transform` 和 `opacity` 只触发合成层变化，不触发回流
5. **读写分离**：避免在修改样式后立即读取布局属性（强制同步布局）''',
    intent: '考察浏览器渲染机制的深入理解和性能优化意识',
    tags: ['渲染机制', '回流', '重绘', '性能优化'],
  ),
  InterviewQuestion(
    id: 'html-06', category: 'HTML/CSS', difficulty: '高级',
    title: '如何实现一个 0.5px 的细线？有哪些方法？',
    answer: '''在高清屏（Retina）上，1 个 CSS 像素可能对应 2-3 个物理像素。实现 0.5px 细线的方法：

1. **transform: scale**（推荐）：
```css
.thin-line {
  height: 1px;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}
```

2. **SVG 绘制**：使用 SVG 的 `stroke-width="0.5"`

3. **viewport + rem**：配合 viewport 缩放实现

4. **border-image / box-shadow**：模拟细线效果

5. **伪元素 + 渐变**：
```css
.thin-line::after {
  content: '';
  display: block;
  height: 1px;
  background: linear-gradient(0deg, #000 50%, transparent 50%);
}
```

`transform` 方案兼容性好，且不影响布局计算，是最推荐的方案。''',
    intent: '考察移动端适配和 CSS 精细控制的实战经验',
    tags: ['CSS技巧', '移动端', '细线'],
  ),
  InterviewQuestion(
    id: 'html-07', category: 'HTML/CSS', difficulty: '中级',
    title: '移动端 1px 边框问题的本质是什么？如何解决？',
    answer: '''**问题本质**：在高 DPR（Device Pixel Ratio）屏幕上，1 个 CSS 像素 = DPR 个物理像素。当 DPR=2 时，CSS 的 1px 边框实际渲染为 2 个物理像素，视觉上比设计稿粗一倍。

**解决方案**：
1. **伪元素 + transform: scale**（最通用）：
```css
.border-1px {
  position: relative;
}
.border-1px::after {
  content: '';
  position: absolute;
  left: 0; bottom: 0;
  width: 100%; height: 1px;
  background: #e0e0e0;
  transform: scaleY(0.5);
}
```

2. **媒体查询 DPR**：根据屏幕 DPR 动态调整 viewport initial-scale

3. **box-shadow** 模拟：`box-shadow: 0 0 0 0.5px #e0e0e0;`

4. **rem + viewport** 全局缩放方案（如 lib-flexible）''',
    intent: '考察移动端适配的实际问题和解决方案',
    tags: ['移动端', '1px', 'DPR', '适配'],
  ),
  InterviewQuestion(
    id: 'html-08', category: 'HTML/CSS', difficulty: '初级',
    title: '请说明 HTML5 语义化标签有哪些？使用它们有什么好处？',
    answer: '''**常用语义化标签**：
- 页面结构：`<header>`、`<main>`、`<footer>`、`<nav>`、`<aside>`、`<section>`、`<article>`
- 内容语义：`<time>`、`<mark>`、`<figure>` + `<figcaption>`、`<details>` + `<summary>`

**好处**：
1. **SEO 友好**：搜索引擎能理解页面结构，提升排名
2. **无障碍访问**：屏幕阅读器能正确解析内容层级
3. **代码可读性**：替代 `<div class="header">` 的语义模糊写法
4. **跨设备适配**：阅读模式、Pocket 等工具能提取核心内容''',
    intent: '考察基础 HTML 功底和 Web 标准意识',
    tags: ['HTML5', '语义化', 'SEO', '无障碍'],
  ),
  InterviewQuestion(
    id: 'html-09', category: 'HTML/CSS', difficulty: '高级',
    title: 'CSS 中有哪些方式可以实现垂直居中？各有什么优劣？',
    answer: '''1. **Flexbox**（最推荐）：
```css
.parent { display: flex; align-items: center; justify-content: center; }
```
优点：简洁、自适应；缺点：IE8- 不支持

2. **Grid**：
```css
.parent { display: grid; place-items: center; }
```
一行代码搞定，浏览器支持好于 Flexbox 在居中场景

3. **绝对定位 + transform**：
```css
.child { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
```
不依赖父容器尺寸，但可能引起模糊（translate 百分比基于自身）

4. **绝对定位 + margin: auto**：
```css
.child { position: absolute; top: 0; left: 0; right: 0; bottom: 0; margin: auto; }
```
需要子元素有固定宽高

5. **table-cell**：传统方案，兼容 IE8，不推荐新项目使用
6. **line-height**：单行文本居中专用''',
    intent: '考察布局方案的知识广度和实际选型判断力',
    tags: ['CSS布局', '垂直居中', 'Flexbox'],
  ),
  InterviewQuestion(
    id: 'html-10', category: 'HTML/CSS', difficulty: '中级',
    title: 'CSS3 动画和 JS 动画的优缺点对比？什么时候用哪个？',
    answer: '''| 维度 | CSS 动画 | JS 动画 |
|------|---------|---------|
| 性能 | GPU 加速（transform/opacity），主线程无关 | 默认在主线程，可能卡顿 |
| 控制力 | 声明式，控制粒度粗（暂停/恢复有限） | 命令式，完全控制帧率和状态 |
| 复杂度 | 简单动画（过渡、关键帧）实现方便 | 复杂序列、物理模拟更灵活 |
| 兼容性 | 不支持 IE9- | requestAnimationFrame 可回退 |

**选择策略**：
- 简单 UI 过渡（hover、展开、淡入）→ CSS transition/animation
- 复杂交互（拖拽、视差、SVG 路径动画）→ JS + rAF
- 需要中断/反向/暂停控制 → JS
- 考虑使用 **Web Animations API** 作为结合两者优势的方案''',
    intent: '考察对动画性能模型的理解和选型判断力',
    tags: ['CSS动画', 'JS动画', '性能'],
  ),

  // ──── JavaScript (10 题) ────
  InterviewQuestion(
    id: 'js-01', category: 'JavaScript', difficulty: '中级',
    title: '请解释 JavaScript 中的闭包（Closure）及其应用场景',
    answer: '''**闭包**：函数能记住并访问其词法作用域中的变量，即使该函数在其词法作用域之外执行。

```javascript
function createCounter() {
  let count = 0;
  return function() {
    return ++count;
  };
}
const counter = createCounter();
counter(); // 1
counter(); // 2  — count 没有被 GC 回收
```

**核心应用场景**：
1. **数据私有化**：模块模式，模拟私有变量
2. **函数工厂**：柯里化、偏函数应用
3. **回调/事件处理**：保存循环中的索引值（经典 `for + var + setTimeout` 问题）
4. **单例模式**：确保全局只有一个实例

**注意事项**：闭包会导致变量无法被 GC 回收，大量使用可能造成内存泄漏。''',
    intent: 'JS 核心概念考察，闭包是面试必问题',
    tags: ['闭包', '作用域', '内存管理'],
  ),
  InterviewQuestion(
    id: 'js-02', category: 'JavaScript', difficulty: '中级',
    title: '请解释原型链（Prototype Chain）的工作机制',
    answer: '''JavaScript 的继承通过原型链实现。每个对象都有一个内部属性 `[[Prototype]]`（通过 `__proto__` 或 `Object.getPrototypeOf()` 访问），指向其构造函数的 `prototype` 对象。

**查找机制**：当访问对象的属性时，先在自身查找 → 找不到则在原型上查找 → 一直向上追溯到 `Object.prototype` → 最终 `null`。

```javascript
function Person(name) { this.name = name; }
Person.prototype.sayHi = function() { return `Hi, I'm \${this.name}`; };

const p = new Person('Alice');
p.sayHi(); // 在 Person.prototype 上找到
p.toString(); // 在 Object.prototype 上找到
```

**ES6 class 语法糖**：本质上仍是原型链继承，只是语法更清晰。`class` 内部还是基于 `prototype`。''',
    intent: '考察 JS 继承机制的深层理解',
    tags: ['原型链', '继承', 'prototype'],
  ),
  InterviewQuestion(
    id: 'js-03', category: 'JavaScript', difficulty: '中级',
    title: '请详细解释事件循环（Event Loop）和宏任务/微任务',
    answer: '''JavaScript 是单线程的，通过 **事件循环** 实现异步非阻塞。

**执行顺序**：
1. 执行全局同步代码（宏任务队列中的第一个任务）
2. 遇到异步操作，将回调放入对应队列：
   - **微任务**（Microtask）：`Promise.then`、`MutationObserver`、`queueMicrotask`
   - **宏任务**（Macrotask）：`setTimeout`、`setInterval`、I/O、`requestAnimationFrame`
3. 当前宏任务执行完毕后，**清空微任务队列**（包括执行过程中产生的新微任务）
4. 渲染更新（如果需要）
5. 从宏任务队列取出下一个任务，回到步骤 1

**经典面试题**：
```javascript
console.log(1);
setTimeout(() => console.log(2), 0);
Promise.resolve().then(() => console.log(3));
console.log(4);
// 输出：1, 4, 3, 2
```''',
    intent: '考察对 JS 异步机制的精确理解，前端面试高频题',
    tags: ['事件循环', '异步', '宏任务', '微任务'],
  ),
  InterviewQuestion(
    id: 'js-04', category: 'JavaScript', difficulty: '中级',
    title: 'Promise、async/await 和 Generator 的区别与联系？',
    answer: '''**Promise**：解决回调地狱的异步方案，提供链式调用和错误传播机制。
```javascript
fetch('/api').then(res => res.json()).then(data => ...).catch(err => ...);
```

**async/await**：Promise 的语法糖，使异步代码看起来像同步代码。
```javascript
async function getData() {
  try { const data = await fetch('/api').then(r => r.json()); return data; }
  catch (err) { console.error(err); }
}
```

**Generator**：可以暂停和恢复的函数（`function*` + `yield`），配合自动执行器可以实现 async/await 的效果（co 库的原理）。

**关系**：async/await 本质上就是 Generator + 自动执行器 + Promise 的语法糖。`await` 后面跟的是一个 Promise。''',
    intent: '考察异步编程方案的演进理解和当前最佳实践',
    tags: ['Promise', 'async/await', 'Generator', '异步'],
  ),
  InterviewQuestion(
    id: 'js-05', category: 'JavaScript', difficulty: '初级',
    title: 'JavaScript 中 this 的指向规则是什么？',
    answer: '''`this` 的值取决于函数调用的方式（调用时确定，非定义时）：

1. **默认绑定**：独立函数调用，`this` → `window`（严格模式下 `undefined`）
2. **隐式绑定**：`obj.fn()` → `this` 指向 `obj`
3. **显式绑定**：`fn.call(obj)` / `fn.apply(obj)` / `fn.bind(obj)` 强制指定
4. **new 绑定**：`new Fn()` → `this` 指向新创建的对象
5. **箭头函数**：无自己的 `this`，继承外层作用域的 `this`（定义时确定）

**优先级**：new > 显式绑定 > 隐式绑定 > 默认绑定

**常见坑**：
- 回调函数中的 `this` 丢失（如 `setTimeout(obj.method, 0)`）
- React class 组件方法需要 `bind(this)` 或用箭头函数''',
    intent: '考察 JS 核心概念 this 的掌握度',
    tags: ['this', '箭头函数', '作用域'],
  ),
  InterviewQuestion(
    id: 'js-06', category: 'JavaScript', difficulty: '初级',
    title: '节流（Throttle）和防抖（Debounce）的区别？分别实现',
    answer: '''**防抖（Debounce）**：高频事件触发后 n 秒内只执行一次，如果 n 秒内再次触发则重新计时。

```javascript
function debounce(fn, delay = 300) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
// 适用：搜索框输入、窗口 resize、表单验证
```

**节流（Throttle）**：高频事件触发后，n 秒内只执行一次，即使持续触发也只按固定频率执行。

```javascript
function throttle(fn, delay = 300) {
  let last = 0;
  return function(...args) {
    const now = Date.now();
    if (now - last >= delay) { fn.apply(this, args); last = now; }
  };
}
// 适用：滚动加载、鼠标移动、按钮防重复点击
```

**关键区别**：防抖是"等你不动了再执行"，节流是"每过一段时间执行一次"。''',
    intent: '考察实际开发中高频事件的性能优化能力',
    tags: ['防抖', '节流', '性能优化'],
  ),
  InterviewQuestion(
    id: 'js-07', category: 'JavaScript', difficulty: '高级',
    title: '深拷贝（Deep Clone）有哪些实现方式？各有什么坑？',
    answer: '''1. **JSON.parse(JSON.stringify(obj))**（最简单）：
   - 无法处理 `undefined`、`Function`、`Symbol`（会丢失）
   - 无法处理循环引用（直接报错）
   - Date 会变成字符串，NaN/Infinity 变 null
   - 只适合纯数据对象

2. **structuredClone()**（原生 API，较新）：
   - 支持 Date、Map、Set、ArrayBuffer 等
   - 仍不支持 Function、Symbol、DOM 节点
   - 浏览器兼容性检查：Chrome 98+

3. **递归实现**（手写）：
```javascript
function deepClone(obj, map = new WeakMap()) {
  if (typeof obj !== 'object' || obj === null) return obj;
  if (map.has(obj)) return map.get(obj);  // 解决循环引用
  const clone = Array.isArray(obj) ? [] : {};
  map.set(obj, clone);
  for (const key of Reflect.ownKeys(obj)) {
    clone[key] = deepClone(obj[key], map);
  }
  return clone;
}
```

4. **lodash.cloneDeep**：生产环境首选，处理了各种边界情况''',
    intent: '考察对不同深拷贝方案的优缺点理解及边界意识',
    tags: ['深拷贝', '数据结构', '边界处理'],
  ),
  InterviewQuestion(
    id: 'js-08', category: 'JavaScript', difficulty: '中级',
    title: 'ES6 模块（import/export）和 CommonJS（require/module.exports）的区别？',
    answer: '''| 维度 | ES Module | CommonJS |
|------|-----------|----------|
| 加载时机 | 编译时静态分析（静态导入） | 运行时加载 |
| 本质 | 引用（live binding） | 值的拷贝 |
| 异步 | 浏览器中天然异步加载 | 同步加载（Node.js） |
| Tree Shaking | 支持（静态分析可做死码消除） | 不支持 |
| 动态导入 | `import()` 返回 Promise | `require()` 可在任意位置调用 |
| this | `undefined` | 指向 `module.exports` |

**关键区别示例**：
```javascript
// ES Module: 导出的是引用，导入方看到的是最新值
export let count = 1;
export function inc() { count++; }

// CommonJS: 导出的是值的拷贝
let count = 1; module.exports = { count, inc() { count++; } };
```''',
    intent: '考察模块化方案的深入理解，常在构建工具相关讨论中出现',
    tags: ['ES6', 'CommonJS', '模块化'],
  ),
  InterviewQuestion(
    id: 'js-09', category: 'JavaScript', difficulty: '高级',
    title: '讲讲 JavaScript 的内存管理和常见内存泄漏场景',
    answer: '''JavaScript 使用**标记清除（Mark-and-Sweep）**垃圾回收算法。从根对象（全局对象）出发标记可达对象，清除不可达对象。

**常见内存泄漏场景**：
1. **意外的全局变量**：未声明的变量自动变为全局属性，永不回收
2. **遗忘的定时器/回调**：`setInterval` 未清除，闭包持有 DOM 引用
3. **DOM 引用残留**：删除 DOM 节点后 JS 中仍持有其引用
4. **闭包不当使用**：大对象被闭包持有，实际不再需要
5. **事件监听未移除**：SPA 页面切换时残留的事件监听
6. **循环引用**：旧 IE 的 COM 对象问题（现代浏览器已解决）

**排查工具**：
- Chrome DevTools Memory 面板：堆快照（Heap Snapshot）+ 时间线分配
- `performance.memory` API（仅 Chrome）
- WeakMap/WeakSet 可作为优化手段''',
    intent: '考察对 JS 内存模型的理解和排查能力',
    tags: ['内存管理', 'GC', '内存泄漏'],
  ),
  InterviewQuestion(
    id: 'js-10', category: 'JavaScript', difficulty: '中级',
    title: 'Array 的 map、filter、reduce、forEach 的区别和使用场景？',
    answer: '''| 方法 | 返回值 | 是否改变原数组 | 适用场景 |
|------|--------|---------------|----------|
| `forEach` | `undefined`（纯遍历） | 否 | 执行副作用（如打印、DOM 操作） |
| `map` | 新数组（1:1映射） | 否 | 对每个元素做变换 |
| `filter` | 新数组（子集） | 否 | 条件筛选 |
| `reduce` | 任意值（累积结果） | 否 | 求总和/平均值、数组扁平化、管道组合 |
| `some` | boolean | 否 | 是否存在满足条件的元素 |
| `every` | boolean | 否 | 是否所有元素都满足条件 |

**性能提示**：多个 `map`+`filter` 链式调用会遍历多次，可考虑合并为 `reduce` 一次遍历。

```javascript
// 不推荐：两次遍历
arr.filter(x => x.active).map(x => x.name);
// 推荐：一次遍历
arr.reduce((acc, x) => { if (x.active) acc.push(x.name); return acc; }, []);
```''',
    intent: '考察数组高阶函数的正确使用和性能意识',
    tags: ['数组', '高阶函数', '函数式编程'],
  ),

  // ──── React/Vue (10 题) ────
  InterviewQuestion(
    id: 'rv-01', category: 'React/Vue', difficulty: '中级',
    title: '虚拟 DOM（Virtual DOM）是什么？为什么需要它？',
    answer: '''**虚拟 DOM** 是真实 DOM 的 JavaScript 对象表示。通过 Diff 算法比较新旧虚拟 DOM，找出最小变更集，批量更新真实 DOM。

**为什么需要**：
1. **性能**：真实 DOM 操作昂贵，虚拟 DOM 将多次操作合并为一次批量更新
2. **跨平台**：虚拟 DOM 是平台无关的抽象层，可渲染到不同目标（DOM、Native、Canvas）
3. **声明式**：开发者描述 UI 状态，框架自动处理 DOM 操作

**Diff 算法核心**（React 为例）：
- 同层比较（不跨层级），时间复杂度 O(n)
- 不同类型节点直接替换整个子树
- 通过 `key` 属性优化列表项的增删移动

**注意**：虚拟 DOM 不是"更快"的方案，它的优势在于在大部分场景下足够快 + 开发体验好。对于极致性能场景，直接操作 DOM（如 Svelte）可能更优。''',
    intent: '考察对框架核心机制的理解，能说清"不是银弹"更显深度',
    tags: ['虚拟DOM', 'React', 'Diff'],
  ),
  InterviewQuestion(
    id: 'rv-02', category: 'React/Vue', difficulty: '高级',
    title: 'React Hooks 的使用规则是什么？为什么需要这些规则？',
    answer: '''**使用规则（Rules of Hooks）**：
1. **只在函数组件顶层调用**，不能在循环、条件或嵌套函数中调用
2. **只在 React 函数中调用**（函数组件或自定义 Hook），普通 JS 函数不行

**为什么需要这些规则**：
React 依赖 Hooks 的**调用顺序**来正确关联状态。每次渲染时 Hooks 按相同顺序调用，React 通过链表结构保存 Hook 状态。

```javascript
// ❌ 错误：条件调用会打乱顺序
if (condition) { useState(0); }  // 第二次渲染可能跳过，状态错位

// ✅ 正确：条件逻辑放在 Hook 内部
const [value, setValue] = useState(0);
if (condition) { /* 使用 value */ }
```

**ESLint 插件** `eslint-plugin-react-hooks` 可以自动检测这些规则违反。''',
    intent: '考察 Hooks 机制的深入理解，而不是死记硬背',
    tags: ['React', 'Hooks', '规则'],
  ),
  InterviewQuestion(
    id: 'rv-03', category: 'React/Vue', difficulty: '中级',
    title: 'Vue 的响应式原理是什么？Vue 2 和 Vue 3 有何区别？',
    answer: '''**Vue 2** 使用 `Object.defineProperty`：
```javascript
Object.defineProperty(obj, key, {
  get() { /* 依赖收集 */ return value; },
  set(newVal) { /* 触发更新 */ value = newVal; dep.notify(); }
});
```
**局限性**：无法检测属性的添加/删除（需要 `Vue.set`/`Vue.delete`），无法直接监听数组索引变化。

**Vue 3** 使用 `Proxy`：
```javascript
new Proxy(obj, {
  get(target, key) { /* 依赖收集 */ return Reflect.get(target, key); },
  set(target, key, value) { /* 触发更新 */ return Reflect.set(target, key, value); },
  deleteProperty(target, key) { /* 触发更新 */ return Reflect.deleteProperty(target, key); }
});
```
**优势**：拦截所有操作（包括新增/删除属性），支持数组方法，更好的 TS 支持，无 `Vue.set` 需求。''',
    intent: '考察 Vue 响应式原理和版本演进的理解',
    tags: ['Vue', '响应式', 'Proxy'],
  ),
  InterviewQuestion(
    id: 'rv-04', category: 'React/Vue', difficulty: '高级',
    title: 'React Fiber 架构解决了什么问题？如何工作的？',
    answer: '''React 15 及之前使用 Stack Reconciler（递归遍历），一旦开始渲染就无法中断，长任务会阻塞主线程导致掉帧。

**Fiber 架构的核心改进**：
1. **可中断的渲染**：将一个大的渲染任务分解为多个小的工作单元（Fiber Node）
2. **优先级调度**：用户交互（高优先级）可中断正在进行的渲染（低优先级）
3. **双缓冲**：current tree 和 workInProgress tree 交替使用

**工作循环**：每个 Fiber 单元执行后检查是否有剩余时间（`requestIdleCallback` 思想），有则继续，无则让出主线程。

**带来的新特性**：
- `Suspense` + `React.lazy`：代码分割 + 优雅的加载态
- Concurrent Mode（React 18 Concurrent Features）：`useTransition`、`useDeferredValue`
- 自动批处理（Automatic Batching）''',
    intent: '考察对 React 架构演进的深层理解',
    tags: ['React', 'Fiber', '架构'],
  ),
  InterviewQuestion(
    id: 'rv-05', category: 'React/Vue', difficulty: '中级',
    title: '前端状态管理方案对比：Redux、Zustand、Pinia、Context 各自适用场景？',
    answer: '''| 方案 | 适用场景 | 优缺点 |
|------|---------|--------|
| **Context + useReducer** | 中小应用，少数全局状态 | 简单零依赖；但频繁更新会导致大面积重渲染 |
| **Redux Toolkit** | 大型应用，需要可预测的状态流 | 完善的 DevTools + 中间件生态；学习曲线较陡，样板代码多 |
| **Zustand** | 中大型应用，追求简洁 | API 极简、无 Provider 包裹、支持 selector 防重渲染 |
| **Pinia** | Vue 生态首选 | Vue 官方推荐，组合式 API 风格，TypeScript 支持好 |
| **Jotai/Recoil** | 原子化状态需求 | 粒度细、天然 code splitting 友好；生态较新 |

**选择建议**：
- 小型项目 → Context 足够
- 追求简洁 + TS 友好 → Zustand
- 团队有 Redux 经验 + 需要中间件 → Redux Toolkit
- Vue 项目 → Pinia 无悬念''',
    intent: '考察状态管理方案的选型能力和项目经验',
    tags: ['状态管理', 'Redux', 'Zustand', 'Context'],
  ),
  InterviewQuestion(
    id: 'rv-06', category: 'React/Vue', difficulty: '中级',
    title: 'React 中性能优化的常用手段有哪些？',
    answer: '''1. **避免不必要的重渲染**：
   - `React.memo`：props 不变时跳过重渲染
   - `useMemo`：缓存计算结果
   - `useCallback`：缓存函数引用（配合 memo 使用）
   - 合理拆分组件，将状态下沉到最小范围

2. **列表优化**：
   - 使用稳定的 `key`（避免 index 作为 key）
   - `useVirtualList`（虚拟滚动，如 react-window）

3. **代码分割**：
   - `React.lazy` + `Suspense` 实现路由级/组件级懒加载
   - `dynamic import()` 按需加载

4. **状态管理优化**：
   - 使用 selector 减少订阅范围
   - Context 拆分（读写分离避免连锁更新）

5. **其他**：
   - 图片懒加载（Intersection Observer）
   - Debounce/Throttle 高频事件
   - Web Worker 处理 CPU 密集型计算''',
    intent: '考察 React 性能优化的实战经验',
    tags: ['React', '性能优化', 'memo'],
  ),
  InterviewQuestion(
    id: 'rv-07', category: 'React/Vue', difficulty: '中级',
    title: 'Vue 的 computed 和 watch 的区别和使用场景？',
    answer: '''| 维度 | computed | watch |
|------|----------|-------|
| 本质 | 计算属性，依赖变化自动重新计算 | 监听器，观察数据变化执行副作用 |
| 缓存 | 是（依赖不变不重新计算） | 否（每次都执行） |
| 返回值 | 必须有返回值 | 不需要返回值 |
| 异步 | 不适合（不支持异步计算） | 支持（适合异步操作） |
| 声明方式 | 函数式，自动追踪依赖 | 需要显式指定监听的源 |

**使用场景**：
- **computed**：模板中需要的派生数据（如格式化价格、过滤列表、全名拼接）
- **watch**：数据变化后执行副作用（如调用 API、操作 DOM、存储到 localStorage、路由变化）

```javascript
// computed: 依赖 firstName 和 lastName 的派生值
const fullName = computed(() => firstName.value + ' ' + lastName.value);

// watch: firstName 变化后发请求
watch(firstName, async (newName) => {
  const result = await api.search(newName);
});
```''',
    intent: '考察 Vue 核心 API 的选择判断力',
    tags: ['Vue', 'computed', 'watch'],
  ),
  InterviewQuestion(
    id: 'rv-08', category: 'React/Vue', difficulty: '初级',
    title: '组件间通信有哪些方式？各自的适用场景？',
    answer: '''**React 组件通信**：
1. **Props 向下传递**：父→子，最基本的通信方式
2. **回调函数向上**：子→父，通过 props 传递回调函数
3. **Context**：跨层级传递（主题、语言、认证状态）
4. **状态管理库**：Redux/Zustand，全局状态共享
5. **Ref**：父访问子的实例或 DOM
6. **Event Bus**（不推荐）：发布/订阅模式，容易失控

**Vue 组件通信**：
1. **Props + Emits**：父↔子标准方式
2. **Provide/Inject**：祖先→后代，功能类似 React Context
3. **Vuex/Pinia**：全局状态
4. **\$refs / \$parent**：直接访问（不推荐，破坏单向数据流）
5. **Event Bus（Vue 2）**：Vue 3 已移除，用 mitt 替代''',
    intent: '考察组件通信方案的广度知识',
    tags: ['组件通信', 'Props', 'Context'],
  ),
  InterviewQuestion(
    id: 'rv-09', category: 'React/Vue', difficulty: '高级',
    title: '前端路由的 Hash 模式和 History 模式有什么区别？',
    answer: '''| 维度 | Hash 模式 | History 模式 |
|------|----------|-------------|
| URL 形式 | `/#/path` | `/path`（无 #） |
| 原理 | `hashchange` 事件 | `pushState`/`replaceState` + `popstate` |
| 服务端配置 | 不需要（hash 不会发到服务端） | 需要配置 fallback（所有路径返回 index.html） |
| SEO | 差（hash 不被爬虫识别） | 好（标准 URL 路径） |
| 锚点 | 冲突（无法使用页面内锚点） | 无冲突 |

**实现要点**：
- History 模式需要 Nginx 配置：`try_files \$uri \$uri/ /index.html;`
- 前端用 `window.history.pushState()` 改变 URL 但不触发页面刷新
- 浏览器前进/后退触发 `popstate` 事件，路由库据此更新 UI
- React Router v6、Vue Router 4 均默认使用 History 模式''',
    intent: '考察前端路由的底层原理理解',
    tags: ['路由', 'SPA', 'History'],
  ),
  InterviewQuestion(
    id: 'rv-10', category: 'React/Vue', difficulty: '高级',
    title: 'SSR（服务端渲染）的优缺点？Next.js/Nuxt.js 解决了什么问题？',
    answer: '''**SSR 优点**：
- SEO 友好：搜索引擎可直接抓取完整 HTML
- 首屏速度快：服务端直接返回 HTML（但 hydration 前不可交互）
- 更好的社交分享预览（Open Graph）

**SSR 缺点**：
- 服务器压力大：每个请求需要渲染完整的页面
- 开发复杂度高：需要处理服务端/客户端代码同构、数据预取、路由同步
- 部署成本高：需要 Node.js 服务器环境
- Time to Interactive（TTI）可能更长：HTML 到达后需要 hydration

**Next.js/Nuxt.js 的解决方案**：
- 文件路由系统：零配置路由
- 混合渲染：SSG（静态生成）+ SSR + ISR（增量静态再生成）可选
- 自动代码分割 + 预加载
- API Routes：内置后端接口能力
- 中间件：请求级别的拦截处理''',
    intent: '考察 SSR 的全局理解和框架选型能力',
    tags: ['SSR', 'Next.js', 'Nuxt.js'],
  ),

  // ──── 算法 (10 题) ────
  InterviewQuestion(
    id: 'algo-01', category: '算法', difficulty: '中级',
    title: '请实现一个快速排序算法，并分析时间复杂度',
    answer: '''```javascript
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = arr.filter(x => x < pivot);
  const mid = arr.filter(x => x === pivot);
  const right = arr.filter(x => x > pivot);
  return [...quickSort(left), ...mid, ...quickSort(right)];
}
// 或者原地排序版本（空间复杂度 O(log n)）
```

**复杂度分析**：
- 最优/平均：O(n log n) — 每次 pivot 都均匀分割
- 最坏：O(n²) — 每次 pivot 都是最大/最小值（已排序或逆序数组）
- 空间：O(log n)（递归栈深度）或 O(n)（非原地版本）

**优化**：随机选择 pivot 或三数取中法避免最坏情况；小数组切换为插入排序。''',
    intent: '考察经典排序算法的掌握程度',
    tags: ['排序', '快速排序', '复杂度'],
  ),
  InterviewQuestion(
    id: 'algo-02', category: '算法', difficulty: '初级',
    title: '如何判断一个链表是否有环？找出环的入口节点？',
    answer: '''**判断有环 — Floyd 判圈算法（快慢指针）**：
```javascript
function hasCycle(head) {
  let slow = head, fast = head;
  while (fast && fast.next) {
    slow = slow.next;
    fast = fast.next.next;
    if (slow === fast) return true;
  }
  return false;
}
```

**找环的入口**：
1. 快慢指针相遇后，将其中一个指针重置到头节点
2. 两个指针都以相同速度（每次一步）前进
3. 再次相遇的节点即为环的入口

**数学原理**：设头到入口距离 a，入口到相遇点距离 b，环长 L。相遇时 slow 走了 a+b，fast 走了 a+b+nL = 2(a+b) → a = nL-b，即从头走 a 步 = 从相遇点走(nL-b)步 = 到达入口。''',
    intent: '考察链表操作和经典算法的数学理解',
    tags: ['链表', '快慢指针', 'Floyd'],
  ),
  InterviewQuestion(
    id: 'algo-03', category: '算法', difficulty: '中级',
    title: '什么是动态规划？请用 DP 解决一个经典问题',
    answer: '''**动态规划（DP）**：将大问题分解为重叠子问题，通过保存子问题的解避免重复计算。

**经典例题：爬楼梯** — 每次可爬 1 或 2 阶，n 阶楼梯有多少种爬法？

```javascript
function climbStairs(n) {
  if (n <= 2) return n;
  let prev2 = 1, prev1 = 2;
  for (let i = 3; i <= n; i++) {
    const curr = prev1 + prev2;  // dp[i] = dp[i-1] + dp[i-2]
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}
```

**DP 解题步骤**：
1. 定义状态（dp[i] 表示爬到第 i 阶的方法数）
2. 找出状态转移方程（dp[i] = dp[i-1] + dp[i-2]）
3. 确定初始条件（dp[1]=1, dp[2]=2）
4. 空间优化（只用两个变量滚动）''',
    intent: '考察 DP 思想和状态转移方程的推导能力',
    tags: ['动态规划', 'DP', '状态转移'],
  ),
  InterviewQuestion(
    id: 'algo-04', category: '算法', difficulty: '初级',
    title: '二叉树的前序、中序、后序遍历（递归+迭代）',
    answer: '''**递归实现**（简单直观）：
```javascript
function preorder(root) { // 根→左→右
  if (!root) return;
  console.log(root.val); preorder(root.left); preorder(root.right);
}
function inorder(root) {  // 左→根→右
  if (!root) return;
  inorder(root.left); console.log(root.val); inorder(root.right);
}
function postorder(root) { // 左→右→根
  if (!root) return;
  postorder(root.left); postorder(root.right); console.log(root.val);
}
```

**迭代实现**（栈模拟）：
```javascript
function inorderIter(root) {
  const stack = [], result = [];
  let curr = root;
  while (curr || stack.length) {
    while (curr) { stack.push(curr); curr = curr.left; } // 一路向左
    curr = stack.pop();
    result.push(curr.val);     // 访问节点
    curr = curr.right;          // 转向右子树
  }
  return result;
}
```''',
    intent: '考察二叉树基本操作，递归和迭代双版本体现思维深度',
    tags: ['二叉树', '遍历', '递归', '迭代'],
  ),
  InterviewQuestion(
    id: 'algo-05', category: '算法', difficulty: '初级',
    title: '两数之和（Two Sum）：给定数组和目标值，找两个数的索引',
    answer: '''**哈希表解法 O(n)**：
```javascript
function twoSum(nums, target) {
  const map = new Map();
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (map.has(complement)) return [map.get(complement), i];
    map.set(nums[i], i);
  }
  return [];
}
```

**暴力解法 O(n²)**：双层循环遍历所有组合（面试中先提暴力再优化到哈希表，展示思维过程）。

**变体**：
- 返回布尔值（是否存在）→ 同样用哈希表
- 数组已排序 → 双指针（左右夹逼）
- 三数之和 → 排序 + 固定一个 + 双指针找另外两个''',
    intent: '考察哈希表的运用和算法优化思维',
    tags: ['哈希表', 'TwoSum', '双指针'],
  ),
  InterviewQuestion(
    id: 'algo-06', category: '算法', difficulty: '中级',
    title: 'LRU 缓存机制的实现思路',
    answer: '''**LRU（Least Recently Used）**：最近最少使用淘汰策略。

**数据结构**：HashMap + 双向链表
- HashMap：O(1) 查找 key
- 双向链表：O(1) 移动节点到头部、删除尾部节点

```javascript
class LRUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.map = new Map(); // JS Map 保持插入顺序
  }
  get(key) {
    if (!this.map.has(key)) return -1;
    const val = this.map.get(key);
    this.map.delete(key);       // 删除
    this.map.set(key, val);     // 重新插入到末尾（最近使用）
    return val;
  }
  put(key, value) {
    if (this.map.has(key)) this.map.delete(key);
    this.map.set(key, value);
    if (this.map.size > this.cap) {
      const oldest = this.map.keys().next().value; // 最久未使用
      this.map.delete(oldest);
    }
  }
}
```

**面试加分**：能讨论实际应用（浏览器缓存、数据库 Buffer Pool、Vue keep-alive）。''',
    intent: '考察数据结构设计的综合能力',
    tags: ['LRU', '缓存', '哈希表', '链表'],
  ),
  InterviewQuestion(
    id: 'algo-07', category: '算法', difficulty: '中级',
    title: '最长无重复字符子串的长度（滑动窗口）',
    answer: '''**滑动窗口 O(n)**：
```javascript
function lengthOfLongestSubstring(s) {
  const map = new Map(); // char → last index
  let left = 0, maxLen = 0;
  for (let right = 0; right < s.length; right++) {
    if (map.has(s[right]) && map.get(s[right]) >= left) {
      left = map.get(s[right]) + 1; // 遇到重复，收缩左边界
    }
    map.set(s[right], right);
    maxLen = Math.max(maxLen, right - left + 1);
  }
  return maxLen;
}
```

**滑动窗口模板**：
1. 右指针扩展窗口
2. 当窗口不满足条件时，左指针收缩
3. 更新结果

**时间复杂度**：O(n)，每个字符最多被左右指针各访问一次。''',
    intent: '考察滑动窗口技巧的运用',
    tags: ['滑动窗口', '字符串', '双指针'],
  ),
  InterviewQuestion(
    id: 'algo-08', category: '算法', difficulty: '高级',
    title: '如何实现一个 Promise.all？考虑异常处理',
    answer: '''```javascript
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    if (!promises.length) return resolve([]);
    const results = new Array(promises.length);
    let completed = 0;

    promises.forEach((promise, index) => {
      Promise.resolve(promise).then(value => {
        results[index] = value;
        completed++;
        if (completed === promises.length) resolve(results);
      }).catch(reject); // 任何一个失败就 reject
    });
  });
}
```

**关键细节**：
1. 用 `Promise.resolve(promise)` 包装，兼容普通值
2. 用数组 + index 保持顺序（不能用 `push`）
3. 任一个 reject 就整体 reject（fail-fast 行为）
4. 可以讨论变体 `Promise.allSettled`（等所有完成，无论成败）和 `Promise.race`

**面试加分**：讨论并发控制（如 `Promise.all` 同时发 100 个请求可能不合理，用并发限制队列）。''',
    intent: '考察对 Promise 机制的深入理解和实现能力',
    tags: ['Promise', '并发', '实现'],
  ),
  InterviewQuestion(
    id: 'algo-09', category: '算法', difficulty: '中级',
    title: '数组扁平化（Flatten），支持指定深度',
    answer: '''```javascript
// 递归方案
function flatten(arr, depth = 1) {
  const result = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      result.push(...flatten(item, depth - 1));
    } else {
      result.push(item);
    }
  }
  return result;
}

// 使用 reduce（更函数式）
function flatten(arr, depth = 1) {
  return arr.reduce((acc, item) =>
    acc.concat(Array.isArray(item) && depth > 0
      ? flatten(item, depth - 1) : item), []);
}

// 完全扁平化（不限深度）— 也可以用 flat(Infinity)
function flattenDeep(arr) {
  return arr.reduce((acc, item) =>
    acc.concat(Array.isArray(item) ? flattenDeep(item) : item), []);
}
```

**注意**：原生 `Array.prototype.flat(depth)` 已支持（ES2019），面试中实现以展示递归思维。''',
    intent: '考察递归思维和数组操作',
    tags: ['数组', '递归', '扁平化'],
  ),
  InterviewQuestion(
    id: 'algo-10', category: '算法', difficulty: '高级',
    title: '如何设计一个短链接系统（TinyURL）？',
    answer: '''**核心需求**：长 URL → 短 URL 的双向映射，短链接访问时 301 重定向到原始 URL。

**短码生成方案**：
1. **Hash 算法**：MD5/SHA256 截取前 6-8 位 + 冲突解决
2. **自增 ID + Base62**：数据库自增 ID 转 62 进制（0-9a-zA-Z），如 `12345 → dnh`
3. **预生成短码池**：提前生成一批短码放 Redis，使用时直接分配

**系统设计要点**：
- **读写比**：读（重定向）远大于写（生成）→ 加缓存（Redis）
- **分库分表**：按短码哈希分片
- **布隆过滤器**：快速判断短码是否已存在
- **限流**：防止恶意频繁生成短链接

**API 设计**：
- `POST /shorten` → `{shortUrl: "abc.xyz/abc123"}`
- `GET /{code}` → 301 重定向到原始 URL''',
    intent: '考察系统设计能力和实际工程思维',
    tags: ['系统设计', 'URL', 'Base62'],
  ),

  // ──── 系统设计 (10 题) ────
  InterviewQuestion(
    id: 'sys-01', category: '系统设计', difficulty: '高级',
    title: '如何设计一个前端监控系统（错误+性能）？',
    answer: '''**核心模块**：
1. **错误监控**：
   - JS 错误：`window.onerror`、`window.addEventListener('unhandledrejection')`
   - 资源加载错误：`window.addEventListener('error', ..., true)`（捕获阶段）
   - 框架错误：Vue `errorHandler`、React `ErrorBoundary`

2. **性能监控**：
   - Navigation Timing API：页面加载各阶段耗时
   - `PerformanceObserver`：监控 LCP、FID、CLS（Web Vitals）
   - Resource Timing：各资源加载耗时
   - 自定义打点：`performance.mark()` + `performance.measure()`

3. **数据上报**：
   - `navigator.sendBeacon()`：页面卸载时可靠上报
   - 1x1 GIF/Image beacon：跨域友好
   - 采样率控制 + 数据聚合（避免海量上报）

4. **Source Map 还原**：上传 sourcemap 到监控平台，线上错误还原到源码位置

**产品化关注点**：错误去重（指纹算法）、影响用户数、上下文信息（用户操作回放）。''',
    intent: '考察前端工程化能力和监控体系建设思路',
    tags: ['监控', 'Sentry', '性能', '错误'],
  ),
  InterviewQuestion(
    id: 'sys-02', category: '系统设计', difficulty: '高级',
    title: '微前端（Micro Frontend）的常见方案和选型考虑',
    answer: '''**主流方案**：
1. **iframe**：最简单，天然沙箱隔离，但 URL 不同步、通信复杂、性能开销大
2. **single-spa**：路由分发 + 生命周期管理，技术栈无关
3. **qiankun（阿里）**：基于 single-spa，增加沙箱（JS 隔离 + CSS 隔离）、资源预加载
4. **Module Federation（Webpack 5）**：运行时加载远程模块，共享依赖
5. **wujie（腾讯）**：基于 WebComponent + iframe 沙箱，更彻底的隔离
6. **Micro App（京东）**：类似 qiankun 但更轻量

**选型考量**：
- **隔离需求**：CSS 隔离（Shadow DOM? CSS Scope?）、JS 隔离（Proxy 沙箱 vs iframe）
- **通信机制**：CustomEvent、共享 Store、URL 参数
- **部署方式**：独立部署 vs 统一构建
- **团队规模**：多团队独立开发是微前端最大的驱动力''',
    intent: '考察微前端架构的深入理解和实践判断力',
    tags: ['微前端', '架构', 'qiankun'],
  ),
  InterviewQuestion(
    id: 'sys-03', category: '系统设计', difficulty: '中级',
    title: '如何设计一个前端脚手架（CLI）工具？',
    answer: '''**核心功能**：
1. **模板管理**：从远程仓库拉取项目模板（git clone / download-git-repo）
2. **交互式配置**：inquirer.js 询问项目名、技术栈、功能选项
3. **模板渲染**：ejs/handlebars 根据用户输入替换模板变量
4. **依赖安装**：自动 npm install 或提示用户

**技术选型**：
- 命令行解析：commander / yargs
- 交互询问：inquirer
- 模板引擎：ejs / handlebars
- 文件操作：fs-extra
- 命令行美化：chalk + ora（loading spinner）

**实际例子**：create-react-app、vue-cli、vite 的 create 命令都是类似的模式。

**进阶能力**：
- `--dry-run` 预览模式
- 插件系统（可扩展更多模板）
- 版本检查 + 自动更新提示''',
    intent: '考察前端工程化工具的构建能力',
    tags: ['CLI', '脚手架', '工程化'],
  ),
  InterviewQuestion(
    id: 'sys-04', category: '系统设计', difficulty: '中级',
    title: '前端 CICD 流水线的设计思路',
    answer: '''**标准流水线阶段**：
1. **代码检查**：ESLint + Prettier → 确保代码风格一致
2. **单元测试**：Jest/Vitest → 跑测试并生成覆盖率报告
3. **构建打包**：`npm run build` → 生产环境产物
4. **部署**：上传 CDN / OSS / 静态服务器
5. **通知**：企微/钉钉/飞书/Slack 通知

**关键设计**：
- **分支策略**：feature → dev → staging → main（不同分支对应不同环境）
- **环境隔离**：开发/测试/预发/生产 环境通过环境变量区分
- **构建优化**：缓存 node_modules、并行构建、增量构建
- **回滚方案**：保留最近 N 个版本，一键回滚到上一版本
- **质量门禁**：覆盖率低于阈值、lint 报错 → 阻断合入

**工具链**：GitHub Actions / GitLab CI / Jenkins + Docker + Nginx''',
    intent: '考察 DevOps 意识和 CI/CD 实践能力',
    tags: ['CI/CD', '自动化', 'DevOps'],
  ),
  InterviewQuestion(
    id: 'sys-05', category: '系统设计', difficulty: '高级',
    title: '大文件上传和断点续传的实现方案',
    answer: '''**核心思想**：将大文件分片（chunk），逐片上传，服务端合并。

**实现步骤**：
1. **文件分片**：`File.slice(start, end)` 每片如 5MB
2. **计算哈希**：SparkMD5 计算文件整体 hash（标识唯一文件）+ 每片 hash
3. **秒传判断**：先发送文件 hash 给服务端，已存在则跳过上传
4. **断点续传**：服务端告知已上传的分片索引，客户端只上传缺失分片
5. **并发上传**：同时上传 3-6 个分片，Promise 并发控制
6. **合并请求**：全部上传完毕后，通知服务端合并分片

**配套能力**：
- 上传进度：`XMLHttpRequest.upload.onprogress` 或 `axios onUploadProgress`
- 暂停/恢复：取消正在进行的请求，保存已上传分片列表
- 文件校验：合并完成后校验文件 hash 完整性

**Web Worker 优化**：分片 hash 计算放 Web Worker 避免主线程阻塞。''',
    intent: '考察文件上传系统的工程化实践',
    tags: ['上传', '断点续传', '分片'],
  ),
  InterviewQuestion(
    id: 'sys-06', category: '系统设计', difficulty: '高级',
    title: '如何设计一个前端低代码平台？核心能力有哪些？',
    answer: '''**核心架构**：
1. **物料体系**：预定义的组件库（表单、图表、布局），每个组件有 schema 描述
2. **画布引擎**：拖拽 → 生成 JSON schema → 实时渲染预览
3. **属性面板**：选中组件 → 右侧展示可配置属性（样式、数据源、事件）
4. **数据源管理**：API 配置、状态管理、变量绑定
5. **代码生成**：JSON schema → 编译生成最终代码（React/Vue 组件）

**技术难点**：
- **拖拽交互**：Drag & Drop API，处理嵌套容器的 drop 区域判定
- **Schema 设计**：如何描述一个组件（props、style、events、children）的元数据
- **渲染/编辑分离**：编辑态（可交互）和预览态（不可交互）的双模式
- **组件通信**：组件间如何传递数据（事件总线、状态提升）
- **回退/重做**：操作历史栈管理

**成熟方案参考**：阿里 lowcode-engine、腾讯 tmagic-editor''',
    intent: '考察低代码平台的架构设计思维',
    tags: ['低代码', '架构', 'Schema'],
  ),
  InterviewQuestion(
    id: 'sys-07', category: '系统设计', difficulty: '中级',
    title: '前端国际化（i18n）方案的设计要点',
    answer: '''**方案设计**：
1. **文案管理**：key-value 的 JSON/YAML 文件，如 `zh-CN.json`、`en-US.json`
2. **翻译函数**：`t('home.title')` → 对应语言的文案
3. **语言切换**：响应式更新（Vue i18n / react-intl 自动重渲染）
4. **持久化**：用户选择存 localStorage，服务端可返回 `Accept-Language` 偏好

**工程化关注点**：
- **文案提取**：CLI 工具扫描代码中的 `t('...')`，自动生成 key 列表
- **翻译管理**：多语言平台（如 Lokalise、Crowdin）统一管理
- **缺失处理**：缺失翻译时显示 key 或 fallback 语言
- **复数/日期/货币**：使用 ICU MessageFormat 或 Intl API

**特殊场景**：
- SSR 中如何确定初始语言（URL 路径 vs Cookie vs Header）
- 动态内容（如富文本中的链接）的翻译处理
- RTL（从右到左）语言的 CSS 处理''',
    intent: '考察国际化方案的系统性思考',
    tags: ['i18n', '国际化', '工程化'],
  ),
  InterviewQuestion(
    id: 'sys-08', category: '系统设计', difficulty: '中级',
    title: '前端安全方面需要注意哪些问题？如何防范？',
    answer: '''**常见安全问题及防护**：
1. **XSS（跨站脚本攻击）**：
   - 不要使用 `dangerouslySetInnerHTML` / `v-html`
   - 用户输入做转义（DOMPurify 库）
   - CSP（Content Security Policy）限制脚本来源

2. **CSRF（跨站请求伪造）**：
   - SameSite Cookie（Lax/Strict）
   - CSRF Token（前后端双重验证）
   - 验证 Referer/Origin 头部

3. **敏感信息泄露**：
   - `.env` 文件不上传 Git
   - 前端不硬编码 API Key/Secret
   - 生产环境关闭 debug/console 输出

4. **依赖安全**：`npm audit` 定期检查，`dependabot` 自动 PR

5. **点击劫持**：`X-Frame-Options: DENY` 防止被 iframe 嵌入

6. **HTTPS**：全站 HTTPS + HSTS 头''',
    intent: '考察安全意识和防护措施',
    tags: ['安全', 'XSS', 'CSRF', 'HTTPS'],
  ),
  InterviewQuestion(
    id: 'sys-09', category: '系统设计', difficulty: '初级',
    title: '如何做前端性能优化？你做过哪些实际优化？',
    answer: '''**性能优化全景图**：
1. **加载优化**：
   - 代码分割（路由懒加载、组件动态导入）
   - 图片优化：WebP 格式、响应式图片（srcset）、懒加载
   - 资源预加载：`preload`（关键资源）、`prefetch`（后续页面资源）
   - CDN + Gzip/Brotli 压缩
   - Tree Shaking 减少打包体积

2. **渲染优化**：
   - 虚拟列表（windowing）处理长列表
   - 防抖/节流 高频事件
   - CSS 动画用 transform/opacity（GPU 加速）
   - 减少重排重绘

3. **缓存策略**：
   - HTTP 缓存（Cache-Control、ETag）
   - Service Worker（PWA 离线缓存）
   - 资源文件名 Hash（长缓存 + 内容变化时更新）

4. **测量工具**：Lighthouse、Web Vitals（LCP/FID/CLS）、Chrome Performance 面板

**回答技巧**：结合真实项目，讲具体做了哪些 + 收效了多少（如 LCP 从 3.2s → 1.1s）。''',
    intent: '考察性能优化的实战经验和方法论',
    tags: ['性能优化', '加载', '缓存', '渲染'],
  ),
  InterviewQuestion(
    id: 'sys-10', category: '系统设计', difficulty: '高级',
    title: '如何设计一个 npm 包？需要注意哪些方面？',
    answer: '''**设计要点**：
1. **API 设计**：简洁直观，符合社区习惯（如函数式 vs 链式调用）
2. **Tree Shaking 支持**：ES Module 导出 + `sideEffects: false`
3. **TypeScript 支持**：提供 `.d.ts` 类型定义
4. **打包策略**：CJS + ESM 双格式（`exports` 字段配置）
5. **版本管理**：严格遵循语义化版本（Semver）
6. **包体积**：排除无用依赖，提供按需引入路径

**工程化配置**：
- `package.json` 的 `main`、`module`、`types`、`exports` 字段
- `.npmignore` 排除源码/测试/配置文件
- CI 自动化发布（semantic-release）
- README + API 文档 + 在线 Demo

**测试与兼容**：
- 覆盖主流 Node.js 版本 + 浏览器环境
- 使用 `browserslist` 声明兼容性
- 含 CI 自动化测试矩阵

**发布前 Checklist**：CHANGELOG、Git Tag、npm publish、通知用户。''',
    intent: '考察开源包设计和工程化能力',
    tags: ['npm', '包设计', '工程化'],
  ),

  // ──── 行为问题 (10 题) ────
  InterviewQuestion(
    id: 'bh-01', category: '行为问题', difficulty: '初级',
    title: '请用 STAR 法则描述一次你解决的最具挑战性的技术问题',
    answer: '''**STAR 法则模板**：
- **Situation（情境）**：项目背景、团队规模、时间压力
- **Task（任务）**：你要解决的具体问题
- **Action（行动）**：你采取的具体步骤（分析→方案→实施→验证）
- **Result（结果）**：量化的成果（性能提升 X%、减少 Y 个 bug、节省 Z 小时）

**回答示例框架**：
"在我负责的电商项目中，首页加载时间在高峰时段高达 5 秒（Situation）。我的任务是将其优化到 2 秒以内（Task）。
我首先用 Lighthouse 分析出主 bundle 过大和图片未压缩是关键瓶颈，然后实施了代码分割（路由懒加载使初始 bundle 减少 60%），配合图片 CDN + WebP 格式 + 懒加载（Action）。
最终 LCP 从 5s 降低到 1.2s，转化率提升了 15%（Result）。"''',
    intent: '考察结构化的沟通能力，STAR 法则在面试中极为重要',
    tags: ['STAR', '沟通', '问题解决'],
  ),
  InterviewQuestion(
    id: 'bh-02', category: '行为问题', difficulty: '初级',
    title: '你如何与产品经理沟通技术方案的可行性？举例说明',
    answer: '''**核心原则**：不说"做不了"，而说"怎么做"和"代价是什么"。

**沟通框架**：
1. **理解需求本质**：先弄清楚 PM 要解决什么用户问题，而不是纠结于具体功能形态
2. **技术方案翻译**：用业务语言（而非技术术语）解释技术约束
3. **给出替代方案**：A 方案（完整实现，需 3 周）、B 方案（MVP 版本，需 1 周）、C 方案（降级方案）
4. **量化影响**：每个方案对用户体验、开发成本、维护成本的影响
5. **共同决策**：让 PM 参与 trade-off，而不是替他们做决定

**示例**：PM 要求 2 周内上线一个复杂功能，技术评估需 4 周 → 提出 MVP 方案（核心流程 2 周可交付），次要功能后续迭代补齐。PM 获得可控的交付节奏，技术团队避免加班赶工。''',
    intent: '考察跨职能沟通和权衡能力',
    tags: ['沟通', '项目管理', 'trade-off'],
  ),
  InterviewQuestion(
    id: 'bh-03', category: '行为问题', difficulty: '中级',
    title: '请描述一次你和同事发生技术分歧的经历，你是如何处理的？',
    answer: '''**健康的分歧处理流程**：
1. **充分倾听**：先让对方完整表达观点，不要打断
2. **理解动机**：分歧背后可能是不同的优先级（性能 vs 开发效率 vs 代码可读性）
3. **数据驱动**：用 benchmark、GitHub issue、社区最佳实践等客观数据支持论点
4. **原型验证**：如果分歧严重，双方各写一个 POC（概念验证）对比
5. **上升决策**：无法达成一致时，请 Tech Lead 或架构师做出最终决策
6. **尊重结果**：决策做出后全力支持，不过后反悔

**避免的行为**：
- 人身攻击或情绪化反应
- "我一直都这么做"的惯性思维
- 在公开场合争论升级（改为 1:1 沟通）

**面试回答要点**：重点是展示你的**协作精神**（不是"我赢了"）和**解决问题的方法论**。''',
    intent: '考察团队协作和冲突解决能力',
    tags: ['团队协作', '冲突处理', '沟通'],
  ),
  InterviewQuestion(
    id: 'bh-04', category: '行为问题', difficulty: '中级',
    title: '你是如何保持技术学习的？请举例说明你最近学的一项技术',
    answer: '''**学习体系建议**：
1. **信息源分层**：
   - 广度：Twitter/X、HN、Reddit、掘金（了解行业动态）
   - 深度：官方文档、源码阅读、技术书籍（系统学习）
   - 实践：Side Project、开源贡献、内部技术分享

2. **输出驱动输入**：
   - 写技术博客（教是最好的学）
   - 团队内做分享演讲
   - 参与开源项目提 PR

3. **时间管理**：每天 30 分钟晨间学习、周末 2 小时深度实践

**回答示例**：
"我最近在学 Rust 和 WebAssembly。起因是我们有个图片压缩功能纯 JS 性能不够好。我花了两周时间用 Rust 写了一个 wasm 模块，将压缩速度提升了 10 倍。过程中我读了 Rust Book、参考了 wasm-pack 文档，最终成功集成到生产环境。"''',
    intent: '考察学习能力和技术热情',
    tags: ['学习', '成长', '自驱'],
  ),
  InterviewQuestion(
    id: 'bh-05', category: '行为问题', difficulty: '中级',
    title: '如果你发现项目中的技术债已经严重影响开发效率，你会如何处理？',
    answer: '''**系统性推进技术债治理**：
1. **量化影响**：技术债造成的具体损失（每次发布多花 X 小时、bug 率高出 Y%）
2. **分类分级**：
   - P0：安全漏洞、影响线上稳定 → 立即修复
   - P1：严重拖慢开发效率 → 纳入下个迭代
   - P2：代码可读性差但功能正常 → Boy Scout Rule（每次顺手改一点）
3. **争取资源**：用数据和业务影响说服 PM/Tech Lead 分配时间
4. **渐进式重构**：
   - 在写新功能时顺带优化相关模块（而非大规模重写）
   - 使用特性开关（Feature Flag）安全上线重构代码
   - 确保有测试覆盖，降低重构风险

**关键思维**：不要追求"完美重写"，而是在**创造业务价值的同时逐步改善代码质量**。''',
    intent: '考察技术管理和推动变革的能力',
    tags: ['技术债', '重构', '项目管理'],
  ),
  InterviewQuestion(
    id: 'bh-06', category: '行为问题', difficulty: '初级',
    title: '你对自己的职业规划是什么？未来 3 年想达到什么目标？',
    answer: '''**回答框架**：
1. **短期（1 年）**：在当前岗位深入某个技术方向（如性能优化、架构设计），成为团队的"Go-to Person"
2. **中期（2-3 年）**：拓展技术广度（如从纯前端拓展到 Node.js/全栈），或向技术管理方向探索（Tech Lead）
3. **长期愿景**：成为能独当一面解决复杂技术问题的资深工程师 / 架构师

**Tips**：
- 具体化目标（不要说"想变得更好"，说"想掌握系统设计能力"）
- 和面试公司的技术栈和发展方向做关联
- 展示你认真思考过自己的职业路径，而不是临时编造的

**示例**：
"短期我想在前端性能优化方面建立深度，成为团队内这个领域的专家。中期我希望拓展后端视野，学习 Node.js 和数据库设计，向全栈方向延伸。同时我也在锻炼技术领导力，希望在 2-3 年内能带领一个小型技术项目。"''',
    intent: '考察职业规划的清晰度和对成长的思考深度',
    tags: ['职业规划', '成长', '目标'],
  ),
  InterviewQuestion(
    id: 'bh-07', category: '行为问题', difficulty: '中级',
    title: '描述一次你主动推动的事情（非上级指派），结果如何？',
    answer: '''**回答要点**：体现自驱力（ownership）和影响力。

**结构化描述**：
1. **发现了什么问题/机会**：你注意到了什么别人没注意到的
2. **为什么是你来做**：虽然不是你的职责，但你觉得重要
3. **你做了什么**：调研→方案→说服团队→落地实施
4. **结果和影响**：量化成果 + 后续是否有推广

**示例**：
"我发现团队每次发布都需要手动操作 10+ 步骤，经常出错导致线上事故。我利用周末研究了 GitHub Actions，搭建了一套自动化 CI/CD 流水线。我找 Tech Lead 做了演示，获得认可后推广到全组。最终发布从 30 分钟减少到 5 分钟，人为错误降为 0。"''',
    intent: '考察主动性和影响力',
    tags: ['主动性', '影响力', 'ownership'],
  ),
  InterviewQuestion(
    id: 'bh-08', category: '行为问题', difficulty: '初级',
    title: '你如何应对工作中的压力和 deadline 紧迫的情况？',
    answer: '''**压力管理框架**：
1. **任务优先级**（Eisenhower Matrix）：
   - 紧急+重要 → 立即做
   - 重要+不紧急 → 计划做
   - 紧急+不重要 → 委派
   - 不紧急+不重要 → 删除

2. **透明沟通**：
   - 提前预警：deadline 可能赶不上时尽早告知，而不是最后一刻
   - 给出方案：列出可以砍掉的范围 + 核心必须交付的部分
   - 请求支持：是否可以有更多资源或调整排期

3. **个人习惯**：
   - 番茄工作法保持专注
   - 分解大任务为小步骤，每完成一个获得成就感
   - 保持规律作息，不长期透支

**回答要点**：展示你的**规划能力**（预防 deadline 压力）和**临场应对能力**。''',
    intent: '考察压力管理和工作方法论',
    tags: ['压力管理', '时间管理', '优先级'],
  ),
  InterviewQuestion(
    id: 'bh-09', category: '行为问题', difficulty: '高级',
    title: '如果你加入一个团队后发现代码质量很差，你会怎么做？',
    answer: '''**思路框架**：
1. **先理解，后改变**：
   - 花 2-4 周了解代码是"为什么烂"的（历史原因？快速迭代？人员流动？）
   - 不要一上来就批评已有代码（你可能不理解当时的约束条件）
2. **建立共识**：和团队讨论"我们理想的代码质量长什么样"，共同制定团队编码规范
3. **工具先行**：引入 ESLint + Prettier + Git Hook（husky + lint-staged），让工具自动保证底线
4. **示范效应**：在新功能中写出高质量代码作为样板，通过 Code Review 传递标准
5. **渐进改进**：每次改一个模块，不要试图大规模重写
6. **知识分享**：组织代码质量相关的 Tech Talk 或 Workshop

**核心心态**：你是来帮助团队变得更好的，不是来证明"你们都是错的"。
**加分项**：能讲出一个真实例子，说明如何把"烂代码"团队引导到"好代码"团队。''',
    intent: '考察领导力、同理心和技术推动力',
    tags: ['领导力', '代码质量', '团队建设'],
  ),
  InterviewQuestion(
    id: 'bh-10', category: '行为问题', difficulty: '中级',
    title: '你在做 Code Review 时主要关注哪些方面？',
    answer: '''**Code Review 检查清单**：
1. **正确性**：逻辑是否正确？边界条件处理了吗？（如空数组、null、错误状态）
2. **可读性**：命名是否清晰？函数是否过长？是否有魔法数字？
3. **设计**：是否符合 SOLID 原则？模块划分是否合理？
4. **性能**：是否有不必要的循环/重复计算？是否造成了不必要的重渲染？
5. **安全性**：用户输入是否做了校验和转义？
6. **测试**：是否有对应的测试？测试覆盖了关键路径和异常情况吗？
7. **一致性**：是否遵循项目现有的代码风格和模式？

**Review 礼仪**：
- 区分"必须改"（blocker）和"建议改"（nitpick）
- 给建设性意见而非指责（"这里可以考虑用 map 替代 for 循环" vs "这里写得太差了"）
- 指出问题的同时给出改进方案
- 对事不对人，用"I think"而非"You are wrong"

**时间管理**：一次 review 不超过 30 分钟，超过说明 PR 太大需要拆分。''',
    intent: '考察 Code Review 的方法论和团队协作意识',
    tags: ['Code Review', '质量', '团队协作'],
  ),
];
