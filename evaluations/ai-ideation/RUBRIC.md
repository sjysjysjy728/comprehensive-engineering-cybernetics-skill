# 评分规则

评测采用 fail-closed 的确定性门禁。全部门禁都必须通过：

1. `SKILL.md` 为纯 idea 请求显式路由到 `ai-ideation.md`，并禁止预载完整科研流程；
2. 已有候选或实现、实验、复现、正式 claim 请求仍路由到 `ai-research.md`；
3. `ai-research.md` 能接收稳定交接包，并在尚未选定候选时返回轻量流程；
4. idea 参考包含问题重构、机制指纹、差异预测、反平庸、普通资源结构假设和停止规则；
5. 交接包包含 `IDEA_ID, OBS_OR_GAP, Q, HYP, RIVAL, PRED, FALSIFIER, CORE, BOUNDARY, CHEAPEST_TEST, EVIDENCE_STATE, NOVELTY_STATE`，且科研流程实际消费问题与否证条件；
6. 创新性状态包含五种受限状态，未检索不得暗示“首次”；
7. 旧单体参考中的 idea 生成章节标题已从 `ai-research.md` 移除；
8. 当前纯 idea 静态指令载荷相对公开基线至少减少 30%；
9. 当前完整科研静态指令载荷不超过公开基线。

脚本检查的是可审计结构和字节数，不能证明 Agent 会遵循这些指令、产生更好的 idea、减少实际 token，或提高真实科研成果。
