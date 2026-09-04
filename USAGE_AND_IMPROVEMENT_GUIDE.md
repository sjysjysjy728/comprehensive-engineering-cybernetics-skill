# 使用、复现与改进指南

这份指南面向两类读者：希望把 `comprehensive-engineering-cybernetics` 用在真实任务中的用户，以及准备提交案例、评测或方法改进的贡献者。第一次接触本项目可先读 [README](README.md)；需要理解 Skill 的路由和共同闭环时读 [SKILL.md](SKILL.md)。

## 先理解能力与证据边界

本 Skill 适合目标复杂、约束明确、需要反复测量和纠偏的工作：合同或需求驱动的项目交付、AI idea 筛选与落地，以及有限资源的组合优化。一步即可完成并验证的低风险改动，通常不需要展开完整闭环。

当前公开证据应按以下边界理解：

- AI idea 的 8 任务三臂测试是探索性开发集比较，不是稳定、普遍有效性的证明；当前版没有通过预注册确认性扩展门。
- 当前版相对无 Skill 和旧版各取得 `3/8` 个 strict win，正反顺序完全一致为 `4/8`；这些结果既不能包装成稳定优势，也不等于 Skill 已被证明无效。
- 每臂每题只有一次候选生成；候选与评委虽然型号不同，仍来自同一模型提供商家族。
- 隔离证据为 `prompt_trace_only`，不是操作系统调用级取证。
- 静态指令文件变短不等于实际 token、时延、GPU 时间或费用下降；本项目目前不声称运行时资源节省。
- 公开的 8 道题、候选、评委输出和匿名映射已经揭盲，只能继续用作公开回归与失效分析，不能再称为盲测或独立确认集。

完整结果与局限见 [8×3 测试报告](evaluations/ai-ideation/behavioral-8x3/RESULT.md)。

## 安装、更新与确认发现

### 使用 Skill Installer

在 Codex 中输入：

```text
$skill-installer 从 https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill.git 安装这个 Skill
```

安装完成后重启 Codex，并输入 `/skills`，确认列表中出现 `comprehensive-engineering-cybernetics`。

### 手动安装

用户级安装：

```bash
git clone "https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill.git" "$HOME/.agents/skills/comprehensive-engineering-cybernetics"
```

只在一个项目中使用时，将仓库放到：

```text
你的项目/.agents/skills/comprehensive-engineering-cybernetics/
```

目录内应直接包含 `SKILL.md`，不要形成 `comprehensive-engineering-cybernetics/comprehensive-engineering-cybernetics/SKILL.md` 的重复嵌套。

### 更新已有安装

若安装目录是 Git 仓库：

```bash
git -C "$HOME/.agents/skills/comprehensive-engineering-cybernetics" pull --ff-only
```

更新后重启 Codex，再用 `/skills` 确认。若仍未发现，依次检查安装层级、目录名、`SKILL.md` 是否存在，以及当前项目是否用同名仓库级 Skill 覆盖了用户级版本。

最后做一次最小调用检查：

```text
$comprehensive-engineering-cybernetics
只判断这个任务应使用哪一种模式，并列出开始工作仍缺少的最小输入；不要执行任务：
目标是在给定代码库中达到一组可测验收指标。
```

预期是识别为项目交付模式并指出缺失输入，而不是凭空补造阈值或直接宣布可完成。

## 四种使用模式

四种模式共享同一个反馈闭环，但输入和裁决不能混用。资源综合也可以作为前三种模式的增强层；只有单体资源不足、组合确有必要时才展开。

### 1. 项目交付模式

适合合同、任务书、技术要求、招标指标、里程碑或正式验收。最低输入是目标材料或要求摘要、硬指标与运行条件、现有工程或资源、预算期限，以及禁止动作或授权边界。

```text
$comprehensive-engineering-cybernetics
使用项目交付模式。
总目标：[最终要交付什么]
合同/要求：[文件位置或脱敏后的逐项要求]
硬指标与验收环境：[阈值、数据、负载、平台、截止条件]
现有资源：[代码、测试、组件、人员、设备及当前基线]
预算与期限：[时间、算力、费用、重试上限]
权限边界：[允许修改/部署什么；未经允许不能做什么]

先建立可追踪要求和真实基线，再实现最小忠实改动；逐项给出证据、未满足项和下一门禁，不得降低阈值换取“完成”。
```

详细规则见 [项目交付闭环](references/project-delivery.md)。

### 2. AI idea 模式

适合尚未选定方案，只需要重构问题、提出和筛选机制候选。最低输入是观察或失败现象、真正目标、可用数据与资源、硬约束，以及这轮输出要支持的决策。

```text
$comprehensive-engineering-cybernetics
只使用 AI idea 快速模式，不展开完整实现或论文实验计划。
观察/失败：[已观察现象、切片差异、当前基线]
目标：[希望改变的真实结果，不只是代理指标]
可用资源：[数据、模型、工具、标注和算力]
硬约束：[隐私、部署、预算、时延、禁止数据或服务]
本轮决策：[从候选中选一个首测 / 判断是否值得继续]

给出机制上不同的候选并去重，最终只保留最优先候选；写清强竞争解释、差异预测、证伪条件和最低成本忠实验证。未知创新性必须标为 not-searched。
```

详细规则见 [AI idea 快速闭环](references/ai-ideation.md)。

### 3. AI 科研模式

适合已有候选，需要做创新性核验、实现、实验、复现或约束论文 claim。最低输入是候选假设与核心机制、目标 claim、代码和数据基线、竞争解释、评测协议、预算与停止条件。若没有稳定候选，应先回到 AI idea 模式。

```text
$comprehensive-engineering-cybernetics
使用 AI 科研模式。
IDEA_ID 与假设：[稳定编号、HYP]
核心机制与边界：[CORE、允许近似、禁止替代]
目标 claim：[成立条件与证据上限]
竞争解释和可证伪预测：[RIVAL、PRED、FALSIFIER]
现有实现与基线：[代码版本、数据切分、指标、已知失败]
资源包络：[GPU、时间、费用、外部检索与数据权限]
评测要求：[主指标、守护指标、公平比较、停止条件]

保持 CLAIM → CORE → IMPL → EXP 可追踪；先做能改变决策的最低保真实验，再报告实现状态、运行有效性、证据裁决和执行决定，不能把代码存在当成 claim 已获支持。
```

详细规则见 [AI 科研闭环](references/ai-research.md)。

### 4. 资源综合模式

适合模型、工具、数据或人员都不顶级，但可能通过互补角色形成更强系统。最低输入是完整目标向量、各资源的实测能力与失效模式、同预算单体基线、组合成本，以及安全回退条件。没有这些测量时，先补基线，不要直接堆叠或投票。

```text
$comprehensive-engineering-cybernetics
使用资源综合模式，并说明它附着于项目交付还是 AI 科研目标。
目标向量：[质量、时延、成本、安全等逐项阈值]
现有资源：[每项资源的版本、窄能力、错误切片和限制]
冻结基线：[相同数据、预算、环境下最强可用单体]
组合包络：[总成本、通信、维护、并行度、部署限制]
共同失效与风险：[相关错误、单点故障、隐私和退出条件]

让每项资源只承担已验证胜任的角色，选择最浅有效结构；用消融、替换和等预算比较验证净增益，并单独给出 GAIN-VERIFIED / NO-GAIN / UNKNOWN。
```

详细规则见 [资源综合与结构增益](references/resource-synthesis.md)。

输入不全时可把未知项明确写成 `unknown`。Skill 应优先提出会改变决策的最小补测，而不是替用户虚构数据、阈值或权限。

## 如何阅读状态输出

不同状态回答不同问题，不应压缩成一个“成功/失败”标签。

| 层面 | 状态 | 正确理解 |
|---|---|---|
| 证据来源 | `observed / sourced / reported / estimated / inferred / unknown` | 说明结论从哪里来；来源明确不自动代表证据有效或适用于目标环境 |
| 项目目标 | `PASS / FAIL / UNKNOWN` | 分别表示全部硬项有合格证据、有效证据表明硬项失败、证据不足或外部结果未知 |
| 项目执行 | `RUNNING / WAITING / STOPPED` | 表示是否仍在推进；可与目标裁决组合，例如目标 `UNKNOWN`、执行 `STOPPED` |
| AI idea 创新性 | `not-searched / near-neighbor-found / overlap-found` 等 | 只表示实际检索边界，不是论文可发表性或新颖性的保证 |
| AI 科研实现 | `not-implemented / coded / mechanically-verified` | 只回答核心机制实现到哪一步，不回答实验是否支持 claim |
| AI 科研运行 | `not-run / unverified-run / valid-run / invalid-run` | 只回答本次运行及协议是否有效 |
| AI 科研证据 | `unclassified / supported-at-Fn / challenged / inconclusive` | 表示证据层级和方向，结论只在声明条件内成立 |
| AI 科研动作 | `CONTINUE / ESCALATE / REDESIGN / NARROW-WITH-AUTHORIZATION / STOPPED` | 表示下一步控制决定，不改变证据本身 |
| 资源组合 | `GAIN-VERIFIED / NO-GAIN / UNKNOWN` | 只裁决冻结比较契约内的系统净增益，不自动等于项目 `PASS` 或科研 claim 获支持 |

看到阶段测试 `PASS`、命令退出码为零或某个均值提高时，应继续检查：它对应哪个边界、全部硬项是否逐项通过、证据是否来自当前目标环境、是否存在无效运行或未授权偏差，以及残余未知是什么。

## 公开 8×3 测试包导航

公开包位于 `evaluations/ai-ideation/behavioral-8x3/`，可从[预注册协议](evaluations/ai-ideation/behavioral-8x3/PROTOCOL.md)或[结果报告](evaluations/ai-ideation/behavioral-8x3/RESULT.md)开始阅读。文件各自承担不同角色：

| 文件 | 用途 |
|---|---|
| [PROTOCOL.md](evaluations/ai-ideation/behavioral-8x3/PROTOCOL.md) | 生成前冻结的目的、三臂设置、隔离边界、前置门、顺序裁决和扩展门 |
| [commitments/prerun.json](evaluations/ai-ideation/behavioral-8x3/commitments/prerun.json) | 预运行版本、模型设置和公开/密封材料的哈希承诺 |
| [TASKS.md](evaluations/ai-ideation/behavioral-8x3/TASKS.md) | 候选实际收到的 8 个封闭世界 AI idea 任务；现已公开，不再是盲测集 |
| [EVALUATOR_KEYS.md](evaluations/ai-ideation/behavioral-8x3/EVALUATOR_KEYS.md) | 评测者边界和每题主要失效风险，不规定唯一正确机制 |
| [RUBRIC.md](evaluations/ai-ideation/behavioral-8x3/RUBRIC.md) | D1–D8 的冻结定义、权重、锚点和客观无效条件 |
| [prompts/CANDIDATE.md](evaluations/ai-ideation/behavioral-8x3/prompts/CANDIDATE.md) | 三臂共用的候选输出与隔离格式 |
| [prompts/JUDGE.md](evaluations/ai-ideation/behavioral-8x3/prompts/JUDGE.md) | 评委 JSON 格式、逐维证据、pairwise 和位置/长度偏差要求 |
| [artifacts/candidates.json](evaluations/ai-ideation/behavioral-8x3/artifacts/candidates.json) | 24 份候选原始输出、逐条哈希、有效性和运行记录 |
| [artifacts/judgments.json](evaluations/ai-ideation/behavioral-8x3/artifacts/judgments.json) | 16 份正序/反序评委原始输出及逐条哈希 |
| [reveal/anonymization.json](evaluations/ai-ideation/behavioral-8x3/reveal/anonymization.json) | 每题 `X/Y/Z` 与三臂的揭盲映射，以及正反呈现顺序 |
| [evaluate.py](evaluations/ai-ideation/behavioral-8x3/evaluate.py) | 只依赖 Python 标准库的确定性哈希、前置门、复算、审计和汇总器 |
| [result.json](evaluations/ai-ideation/behavioral-8x3/result.json) | 机器可读权威汇总、逐题结果、敏感性分析、质量审计和限制 |
| [RESULT.md](evaluations/ai-ideation/behavioral-8x3/RESULT.md) | 面向人的结论、失败门、反例和证据边界 |

不要直接改写冻结协议、原始 artifact 或现有 `result.json` 来让分数变好。新的行为证据应使用新的评测 ID 和目录，并保留旧结果。

## 确定性复现

以下命令在仓库根目录运行，只需 Python 标准库。`-I -B` 分别减少环境注入并禁止写入字节码缓存，`-X utf8` 固定文本编码。

先复算 8×3 结果并逐字节核对公开机器结果：

```bash
python -X utf8 -I -B evaluations/ai-ideation/behavioral-8x3/evaluate.py --check result.json
```

关键输出应为：

```text
PASS CEC-AIIdea-8x3-Dev-1: result.json = 5a64c853fb19fe14f77d53e3c47623de0aede3ed576187f3dea59fa4988d3542
```

再运行全部公开评测：

```bash
python -X utf8 -I -B evaluations/run_all.py
```

输出 JSON 应包含 `"status": "PASS"`、`"passed": 5` 和 `"failed": 0`，即 `5/5` 项通过。这里的 `PASS` 表示公开 artifact、计算与结构回归一致，不表示 Skill 已经稳定优于对照。

贡献前还应运行发布校验：

```bash
python -X utf8 -I -B ci/validate_release.py --self-test
python -X utf8 -I -B ci/validate_release.py --repo . --skill .
```

本指南进入发布清单后的关键输出应分别包含 `SELF-TEST PASS (22 assertions)` 和 `VALIDATION PASS (64 files, ... bytes)`。文件数不同通常表示发布清单遗漏、存在多余文件，或你正在复现不同提交；先核对所检出的版本，不要为了匹配数字删除未知文件。

### CI 能复现什么，不能复现什么

CI 能确定性核对预注册文件和公开材料的哈希，重新执行候选前置门、冻结权重总分复算、pairwise 归一化、顺序与长度诊断、扩展门，以及其他四项公开回归。

CI **不能重放模型生成本身**。仓库冻结的是已经产生的 24 份候选和 16 份评委输出；CI 不会重新调用当时的模型，也无法复原随机采样、服务端实现、fresh-context 平台状态、模型提供商内部版本，或缺失的 token 与墙钟记录。因此：

- 哈希和聚合复现成功，只证明“给定这些公开输入和原始输出，审计结果可重复”；
- 它不证明再次调用模型会生成相同文本；
- 它不把原始主观评审自动变成无偏真值；
- 它不支持运行时节省声明。

## 用公开任务做回归与失败分析

公开八题适合发现已知能力是否退化，不适合证明新版本泛化。推荐流程如下：

1. 先在未修改仓库上运行上述确定性命令，记录提交号、结果 SHA 和 `5/5` 基线。
2. 从 [result.json](evaluations/ai-ideation/behavioral-8x3/result.json) 选择一个真实失败，区分候选格式失败、硬约束失败、D1–D8 某一维下降、正反顺序不一致、长度相关或评委证据错误。
3. 回看对应的 [任务](evaluations/ai-ideation/behavioral-8x3/TASKS.md)、候选原文、评委原文和 [量表](evaluations/ai-ideation/behavioral-8x3/RUBRIC.md)，写出可以被新证据推翻的根因假设。不要只根据总分猜原因。
4. 在新目录或临时分支保存新候选、评委输出和聚合结果，不覆盖现有冻结 artifact；保留失败原文和所有无效运行，不做质量驱动重试。
5. 修改后重跑全部公开回归，确认已知能力没有倒退；再用从未向修改者公开的新密封任务做独立前向测试。

IDEA-03 和 IDEA-07 是目前最明显的当前版反例，可以用于定位“目标版本语义与冲突证据处理”和“评价器循环、记忆与真实下游效用”等失效类别，但不要把题目词汇、阈值、数据规模或期望答案写进 Skill。任何专门识别 `IDEA-03`、`IDEA-07` 或八道公开题表面特征的规则都属于过拟合。改进应描述可迁移的决策原则，并至少在同类全新密封题与不同领域题上验证。

## 推荐的改进闭环

一次可信改进至少完成下面的闭环：

1. **先复现。** 固定代码提交、Skill 版本、运行命令与现有结果；不能复现时先解决环境或证据问题。
2. **定位失败。** 从原始输出和逐维证据判断是路由、指令、格式、核心机制、硬约束、评测协议还是评委失效。
3. **做最小改动。** 修改能解释失败的最小规则或结构；避免为了一个样例继续堆叠提示词。
4. **跑旧回归。** 运行 8×3 确定性复算、全部 `5/5` 公开评测和发布校验；保留任何退化。
5. **准备全新密封任务。** 任务不能被修改者或候选提前看到，并应覆盖目标失效类别及不同领域的反例。
6. **先预注册再生成。** 在生成候选前冻结任务、输出限制、候选臂、模型和推理配置、允许重试条件、无效候选处理、量表、主要统计单位、成功门与停止条件，并留下公开哈希承诺。
7. **使用匹配基线。** 各臂使用相同任务、模型、推理强度、输出上限、预算、工具权限和运行环境；有意差异只能是待测 Skill 指令。保留无 Skill、上一版本和必要消融。
8. **进行多次重复。** 每题每臂使用预先冻结的多个独立重复或种子，按任务而不是输出条数作为主要统计单位；报告方差和失败率，不挑最好一次。
9. **审计顺序、长度与评委偏差。** 匿名随机映射，使用正反或平衡顺序、独立评委和允许平局的 pairwise；机械复算总分，核对引文是否为精确原文，报告位置效应、答案长度与评分关系及评委间一致性。
10. **实测资源。** 若主张节省资源，预先定义采集方式并记录每臂可比较的 input/output/cache/reasoning token、墙钟时间、GPU 时间、显存、费用和重试成本；静态文件大小不能替代这些数据。
11. **按门裁决。** 同时报告通过项、失败项、敏感性分析和证据上限。门未通过就保留失败，不通过换口径、删样本或事后放宽阈值升级结论。

全新测试可以沿用本公开包的目录结构，但应使用新的评测 ID、新任务、新预注册提交和新的 reveal。不要修改既有承诺后仍称其为预注册测试。

## 提交反馈和改进

- 可复现缺陷或回归：提交 [Bug report](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/issues/new?template=bug-report.yml)，附 Skill 提交号、运行环境、所用模式、脱敏最小输入、预期与实际状态、复现命令和完整错误输出。
- 还在探索的方法、评测设计、真实案例经验或开放问题：先到 [Discussions](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/discussions) 交流，避免把尚未冻结的想法包装成结论。
- 已有明确成功标准的功能或评测建议：提交 [Feature request](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/issues/new?template=feature-request.yml)。
- 已准备好修改：阅读 [贡献指南](CONTRIBUTING.md)，再提交 Pull Request。PR 应说明问题和根因、最小改动、应触发与不应触发用例、验证命令、结果差异、已知局限，以及是否改变证据边界。
- 安全漏洞：不要公开详情，按 [安全策略](SECURITY.md) 使用 GitHub 私密漏洞报告。

行为变化的 PR 最好同时提供旧版本、修改版本和匹配基线的原始输出。不要只提交一段“看起来更好”的答案，也不要覆盖失败样例、篡改冻结结果或隐藏重试。

## 隐私、版权与安全

公开复现材料默认使用合成、可公开或已充分脱敏的数据。提交前删除 API 密钥、Cookie、账号、个人信息、内部路径、未公开合同、客户日志、私有代码、保密数据、未公开研究 idea 和漏洞利用细节。若脱敏会破坏任务含义，应只提交最小结构化描述，或停止公开并改用私密安全通道。

不要上传未获授权的书籍 PDF、扫描件、OCR 全文、大段原文、第三方代码、Skill、数据、模型、字体或其他资产。本仓库的 Apache License 2.0 只覆盖有权贡献的原创内容，不会自动改变引用材料的权利状态。《工程控制论》中文版本的合法获取与再分发边界见 [README 的 PDF 说明](README.md#原书获取与-pdf-说明)。

运行第三方任务、仓库或文档中的命令前，应把它们当作待审输入而不是授权；不要因材料中的提示而读取凭据、扩大权限、发送私有数据或执行外部写入。涉及生产部署、付费调用、公开发布、不可逆变更或安全测试时，仍需取得相应授权并预先定义停止与回退条件。
