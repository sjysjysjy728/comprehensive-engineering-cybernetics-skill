# AI idea 渐进披露结构回归

目标：验证当前发布包是否把纯 idea 请求与完整科研执行流程分离，并保留生成质量、反平庸、普通资源结构增益和实现交接所需的不变量。

本评测只读取仓库中的 `SKILL.md`、`references/ai-ideation.md` 和 `references/ai-research.md`。它不调用模型、不联网、不读取其他本地 Skill，也不生成研究 idea。

比较基线是公开提交 `3278710dc8a141a5ecb9a7651c86ea2b9da631e6` 中纯 AI 请求会加载的 `SKILL.md + references/ai-research.md`，合计 25,062 个 UTF-8 字节。当前纯 idea 路径按 `SKILL.md + references/ai-ideation.md` 计算；另行报告同一上下文先加载 idea、再加载完整科研参考时的累计载荷，不用快速路径的局部改善掩盖端到端增加。该口径只衡量静态指令载荷，不等于运行时 input token、缓存 token、费用或端到端质量。

任务成功条件见 [RUBRIC.md](RUBRIC.md)。公开后，本任务只能作为发布结构回归，不能作为盲测或 Skill 效果证明。
