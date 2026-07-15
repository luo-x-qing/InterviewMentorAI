# 全局强制性指令

## 1. 语言要求
默认使用中文回复，所有对话、解释、代码注释和思考过程均使用中文。

## 2. 技能自动匹配与强制执行 (Critical)
在回答用户任何问题之前，**必须**先执行以下步骤：
1. 检查 `.agents/skills/` 目录下的所有技能（Skills）。
2. 判断用户的问题属于哪个技能的范围（例如：问代码架构 -> 查看 `codebase-design`；问 Bug -> 查看 `diagnosing-bugs`；问实现代码 -> 查看 `implement`）。
3. **只有在阅读并理解了对应技能的全部指令后，才能开始思考并回复用户。**
4. 如果找不到完全匹配的技能，也必须查看 `find-skills` 或 `wayfinder` 来寻求指引。
5. 严禁脱离技能规范直接给出泛泛的答案。

---

# Agents

> 默认语言为中文，所有回复、解释和代码注释建议均使用中文。

## Agent skills

### Issue tracker

GitHub Issues via `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Multi-context — root `CONTEXT-MAP.md` + per-package `CONTEXT.md` files. See `docs/agents/domain.md`.
