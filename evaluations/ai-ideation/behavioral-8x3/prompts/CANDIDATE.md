# 冻结候选提示

你正在参加一次受控的离线回答测试。只使用本消息中提供的 instruction bundle（若有）和任务正文。不得调用或读取任何其他 Skill、文件、工具、网页、外部资料或子 Agent，也不得使用跨运行记忆。不要提及测试条件、instruction bundle 或评测过程。

完成任务正文要求，并严格返回一个 JSON 对象，不要使用 Markdown 代码围栏或添加 JSON 之外的文字：

```json
{
  "answer": "你的完整回答",
  "isolation_attestation": {
    "used_tools": false,
    "read_files": false,
    "used_web": false,
    "used_other_skills": false,
    "used_subagents": false,
    "used_cross_run_memory": false
  }
}
```

`answer` 的长度上限以任务正文为准。JSON 外壳不计入该上限。

## 任务正文

{{TASK_PROMPT}}
