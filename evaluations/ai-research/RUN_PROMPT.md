# 历史运行提示与隔离条件

以下是修复后定向回归使用的候选提示。初始 A/B 使用相同文本，但没有第 6 条 Windows PowerShell 5 UTF-8 读取要求。对照条件禁用全部本地 Skills；处理条件只启用 `comprehensive-engineering-cybernetics`，其余 Skills 禁用。

```text
$comprehensive-engineering-cybernetics

Complete the frozen TASK.md in the current directory and use RUBRIC.md as the scoring boundary. Edit only submission.json; the supplied code and data are read-only test inputs.

This is a matched independence test:

1. If the named Skill is available, use only that Skill and only its SKILL.md plus the AI-research reference it explicitly routes to. If it is unavailable, continue without any Skill and do not search for one.
2. Do not read or use any other Skill, editor extension content, book/PDF/OCR, repository, prior candidate, or file outside this candidate workspace.
3. Do not browse the web, call apps/connectors, install packages, or create subagents.
4. Use only the supplied Python standard-library evaluator. You may run python -I -B evaluate_public.py submission.json while iterating.
5. Keep the three ideas genuinely distinct, freeze one falsifiable hypothesis and rival, preserve the selected mechanism in the DSL, and report only recomputed public evidence.
6. On Windows PowerShell 5, read UTF-8 Markdown and JSON with Get-Content -Raw -Encoding UTF8; if any text is garbled, reread it correctly before acting.
7. Use at most 32 tool calls. Stop after the public evaluator passes or after you can honestly report the remaining blocker; never weaken a threshold or edit a frozen file.

In the final response, state the public evaluator result, selected mechanism, claim/evidence ceiling, and any unresolved limitation. Do not identify the run condition.
```

## 历史执行控制

- 候选从相同的冻结输入开始，只有 `submission.json` 可写；
- 初始测试的候选目录名称暴露了 `baseline` / `target` 标签，这是已披露偏差；定向回归改用中性 `Q` / `R`；
- 运行器使用临时会话、忽略用户配置和规则，并显式配置 Skill 开关；
- 候选冻结后才揭示已承诺的 held-out 生成种子；发布包不包含私有种子；
- 两位盲评判官在新上下文中交换候选位置；它们与候选属于同一 Codex 模型家族；
- 没有系统调用级网络/文件系统隔离证明，也没有对模型、解码、CPU、内存和输出上限做取证级同一性证明；
- 本地 Codex 由 VS Code 扩展打包，但提示明确禁止读取编辑器扩展内容和其他 Skills。上述控制降低污染风险，不等于形式化隔离证明。

## 公开复核

本目录不重新发布冻结数据、运行器、原始轨迹或私有种子。公开审计命令只使用 Python 标准库：

```bash
python -I -B evaluate.py --check result.json
```

它严格解析 JSON，复核示例提交哈希、三个 Idea Card、模型成本、主效应嵌套、历史 15/15 门禁记录、关键指标、token、盲评算术和裁决边界。它不重新运行候选模型或隐藏数据。
