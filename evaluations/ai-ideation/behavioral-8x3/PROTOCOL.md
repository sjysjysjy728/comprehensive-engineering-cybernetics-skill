# CEC-AIIdea-8x3-Dev-1 预注册协议

状态：`preregistered`。本协议与哈希承诺必须在任何被计分候选生成前进入公开 Git 历史；后续只新增 reveal、运行结果和审计文件，不回写本协议。

## 目的与证据上限

在 8 个封闭世界 AI idea 任务上比较三个条件：无 Skill、上一公开版本和当前轻量版本。唯一有意差异是提供给生成器的 instruction bundle：

- `no_skill`：不提供 Skill；
- `legacy`：提交 `3278710dc8a141a5ecb9a7651c86ea2b9da631e6` 的 `SKILL.md + references/ai-research.md`；
- `current`：提交 `43501b979d47dc83ebe59e35154cbb27f26141d5` 的 `SKILL.md + references/ai-ideation.md`。

统计单位是 8 个配对任务，不是 24 份候选或评委次数。每个条件每题只生成一次，因此结果最多是该冻结开发集上的探索性比较；无论结果多强，都不能证明普遍优势。

## 冻结运行条件

- 候选生成器：`gpt-5.6-sol`，reasoning effort `high`，每次 `fork_turns=none` 的新 Agent；
- 评委：`gpt-5.5`，reasoning effort `high`，与候选生成器型号不同；
- 每题三臂获得完全相同的任务正文、输出上限和共同候选提示；
- 禁止候选联网、调用工具、读取文件、调用其他 Skill、调用子 Agent或跨运行记忆；
- 一次运行只回答一道题；不得因答案质量重试。只有空输出或平台错误允许一次重试，原失败记录仍保留；
- 隔离等级固定为 `prompt_trace_only`：提示和 Agent 轨迹可检查，但没有操作系统调用级取证，不得称为严格沙箱隔离；
- 平台不提供可核对的 input/cache/reasoning token 与墙钟记录时，资源字段写 `unavailable`，不推断运行时节省。

## 冻结与揭盲

候选生成前冻结任务包、评测者说明、候选提示、评委提示、量表、匿名映射和顺序，并在 `commitments/prerun.json` 记录 SHA-256。任务包、评测者说明和映射在候选与评委全部完成前仅保存于 Git 忽略目录。评委只看到中性标签 `X/Y/Z`；每题标签映射不同。正序按 `X,Y,Z`，另一名 fresh 评委按精确反序 `Z,Y,X` 阅读；映射在两个评委输出冻结后揭示。

## 确定性前置门禁

进入主观评分前，每份候选必须：

1. 是严格 UTF-8、无 BOM 的单个 JSON 对象，无重复键和非有限数；
2. 只含 `answer` 和 `isolation_attestation`，且所有隔离布尔值均为 `false`；
3. `answer` 非空且不超过对应题目的 Unicode code-point 上限；
4. 不出现条件名、Skill 名、提交号、本地路径、外部 URL 或未下发的评测内容；
5. 没有平台失败或质量驱动的重试。

语义上的预算、数据、隐私或部署违规由评委按硬约束维度审计，并在明显违规时标为 `objective_invalid`；高总分不能覆盖硬违规。

## 评审与顺序裁决

每位评委先为三个候选逐维引用原文证据，再按 [冻结量表](RUBRIC.md) 给 0–4 分并计算加权百分制；不得奖励篇幅、自信语气或 Skill 术语。之后独立比较三对候选，可判平局。

某一顺序中，两候选只有在 pairwise 胜负与总分方向一致且领先至少 5/100 时才记为胜，否则记平。两个顺序对同一 pair 均给出同一胜者、两次差值均至少 5 且总分跨顺序波动不超过 8，才记 `strict_win`；一胜一平记 `low_confidence_lean`；胜者相反、两次均平或 pairwise 与分数冲突记 `tie_low_confidence`。不得用平均分覆盖顺序不一致。

## 汇总与扩展门

公开逐题有效性、三臂分数、两条 current 配对差值、各维度中位差、strict win/lean/tie/loss、顺序一致率、候选长度，以及长度与分数的诊断关系。8 题太少，不把相关系数或符号检验解释成总体统计证明。

只有同时满足以下条件，才记为 `pass_for_confirmatory_expansion`：

- current 客观有效题数至少 7/8，且无泄露或安全硬失败；
- current 对 no_skill 与 legacy 分别至少取得 7/8 个 strict win；
- 对两个基线的逐题总分差中位数均至少 +5；
- 问题重构、机制、差异预测/证伪、最低成本验证、约束五个关键维度的配对中位差均不为负；
- 至少 7/8 题的两个阅读顺序一致，且没有未解决的长度混杂警报。

未通过只表示本冻结开发集没有达到扩展门，不等于 Skill 无效。运行时节省独立裁决；没有可比 token/墙钟证据时固定为 `runtime_savings_not_supported`。
