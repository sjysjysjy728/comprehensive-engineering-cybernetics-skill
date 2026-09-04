# 最全面工程控制论 Skill：面向工程与 AI 领域科研

> 用工程控制论的思路，把复杂任务变成可测量、可纠偏、能验收、不过度消耗资源的反馈闭环。

> 独立社区项目；不是 OpenAI 或《工程控制论》的官方发布、阐释或认证工具。

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Release quality gate](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/actions/workflows/quality-gate.yml/badge.svg?branch=main)](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/actions/workflows/quality-gate.yml)

`comprehensive-engineering-cybernetics` 是一个面向 Codex 的中文 Agent Skill。它不是控制理论教材，而是一套可执行的工作方法：先固定目标和硬约束，再识别现有资源与真实基线，用最小但不失真的行动取得反馈，持续修正偏差，最后用证据判断是否真正完成。

它主要服务三类任务：

- **工程项目交付**：从合同、任务书或技术要求出发，实现功能并逐项达到验收指标；
- **AI 科研**：从问题与 idea 出发，形成可区分的假设，忠实实现核心机制，并用可信实验约束结论；
- **资源综合**：把能力有限、并非顶级的模型、代码、工具、数据和人员安排到合适角色，通过互补、校验、隔离和切换争取优于单一资源的整体效果。

这里的“最全面”表示本项目试图覆盖“项目交付—AI 科研—资源综合”的完整链路，不代表第三方排名、基准第一或 SOTA 声明。

## 与最初目标逐项验收

结论先行：作为一个公开、可安装、可回归并带反馈通道的 Skill 工程，发布目标已经满足；作为“在不同任务上都能带来更好结果且更省资源”的普遍有效性证明，目前**没有全部满足**。下表把“方法是否已经写入 Skill”和“效果是否已经被独立证据支持”分开，避免用功能存在代替效果证明。

| 最初目标 | Skill 中的机制 | 当前效果证据 | 当前裁决 |
|---|---|---|---|
| 根据合同和要求实现功能、逐项达到指标 | 已实现要求编译、基线、追踪、变更控制、分段闭环和验收门禁 | 一个冻结合成修复任务从历史起点 `8/52` 达到 `52/52`；缺少匹配的无 Skill 修复对照 | **受限条件下满足** |
| 帮助产生更好的 AI idea | 新增轻量的“问题重构 → 机制种子/指纹去重 → 差异预测 → 反平庸 → 双轨筛选”闭环 | 预注册 8 任务三臂测试中，当前版 8/8 有效、中位分 `93.0`，高于无 Skill 的 `89.0625` 和旧版的 `87.125`；但相对两个对照均只有 `3/8` strict win，未通过确认性扩展门 | **有跨任务正信号，稳定优势未证明** |
| 实现 idea 时不打折扣 | 新增 `IDEA_ID/HYP/RIVAL/PRED/FALSIFIER/CORE` 最小交接包，并保留 `CLAIM → CORE → IMPL → EXP` 双向链 | 初测发现并保留了非嵌套模型错误；结构层级门已闭合该已知错误，但新交接包尚待未公开任务确认 | **结构已实现，待全新独立确认** |
| 节省 token、算力、时间或总成本 | 纯 idea 与完整科研流程改为渐进披露，并保留预算、多保真、早停和缓存控制 | 纯 idea 静态指令载荷从 25,062 降到 17,326 UTF-8 字节（−30.867449%）；8 任务测试无可核对 token/墙钟数据，旧行为运行的 input token 仍增加 `56.18%–82.77%` | **静态载荷改善；运行时节省未证明** |
| 用已有、有限、非顶级资源得到更好效果 | 已实现角色标定、互补/共同失效检查、最浅结构、等预算基线、消融和隔离 | 固定合成基准中三资源组合 exact `0.80`，等预算单资源 `0.35–0.40`，结构与安全门禁全部通过 | **固定基准内满足** |
| 独立测试，尽量不使用其他本地或 VS Code 类似 Skill | 已实现一次性配置、显式目标 Skill 和非目标 Skill 禁用 | 8 任务测试的 24 次候选与 16 次评委运行均使用 fresh context，并在提示与轨迹层禁用工具、文件、网络和其他 Skill；隔离等级仅为 `prompt_trace_only`，不是系统调用级取证 | **提示与轨迹级满足，非取证级** |
| 面向用户的 README、参考披露、反馈通道和干净公开边界 | 已实现使用说明、来源/原创边界、Issues、Discussions、私密安全报告和发布白名单 | 远端设置已核对；63 个公开文件与白名单一致，下载仓库、私有规划材料和本地路径未上传 | **满足** |
| 提供中文 PDF 的合法获取方式 | 已提供出版社购买与受控阅读入口，并设置再分发授权门 | 当前文件未发现允许公开再分发的许可，因此没有上传 PDF | **合法获取满足；公开托管待授权** |

所以，本仓库可以诚实地说“主要控制结构均已写入发布包，而且 AI idea 已完成预注册、三臂、8 任务的跨任务测试”；也必须同时保留其失败裁决：当前版只取得两组各 `3/8` strict win、顺序完全一致仅 `4/8`，没有通过确认性扩展门。不能据此声称它普遍优于不用 Skill 的方法，也不能声称已经实现运行时资源节省。下一轮应针对明确反例做小修订，并换用全新未公开任务、多次重复和更强隔离重新确认。

## 公开评测：我们实际证明了什么

公开评测展示的是受限行为、探索性信号和发布结构，而不是普遍优势。AI idea 现在有一个预注册的 8 任务三臂行为测试，并保留更早的单任务 pilot 和结构回归；另外，在一个冻结工程合同上逐项达到 `52/52`，在一个合成、等预算资源任务上通过角色分工获得经穷举验证的结构增益，在 AI 科研任务上保留初始 A/B 负结果并闭合一个已知缺陷。

| 模式 | 已观察结果 | 能支持的结论 | 不能支持的结论 |
|---|---|---|---|
| AI idea 快速路径 | [预注册 8 任务三臂测试](evaluations/ai-ideation/behavioral-8x3/RESULT.md)中当前版/无 Skill/旧版中位分为 `93.0/89.0625/87.125`，当前版 8/8 有效；但相对两对照 strict win 均为 `3/8`，顺序一致 `4/8`，确认性扩展门未通过。9/9 结构门和更早的单任务 pilot 仍保留 | 当前版在问题重构、机制、证伪和最低成本验证等关键维度给出跨任务正向信号，也暴露了需要优先修正的 IDEA-03/07 反例 | 不证明稳定或普遍优于对照；旧版有 2 个无效候选，评委结果需要机械复算，且没有真实实验或运行时成本证据 |
| 项目交付 | 缺陷程序历史起点 `8/52`；显式调用 Skill 的运行达到 `52/52`；公开代码可复跑 `52/52`；历史独立评分 `100/100` | 这一次运行逐项闭合了冻结需求，并产出可执行、可复核的交付物 | 无匹配的无 Skill 修复对照；公开包不能重建历史起点或重算过程分；不代表所有项目 |
| AI 科研 | 初始 A/B 两边均过 `15/15` 机器门禁，但无 Skill 基线在反转顺序盲评中均分 `100`，Skill 条件为 `70`；修复后定向回归两边均为 5 项、成本 7、指标完全相同，盲评规则判为平局 | 初始结果成功暴露模型—主张层级错误；新增结构层级门后，这个固定错误已闭合，且仍保持可证伪假设、隐藏分割和证据上限 | 初始结果不支持 Skill 质量优势；定向回归受该基准启发，不是独立泛化或因果证明；也没有节省端到端 token |
| 资源综合 | 三项互补资源在 2,000 个合成样本上精确匹配 `0.80`，等预算单资源为 `0.35–0.40`；10/10 分片、消融、替换、安全与 27 种来源组合穷举均通过 | 本次产出的三角色、单层、3-credit 结构在固定基准内具有客观净增益，状态为 `GAIN-VERIFIED` | 没有无 Skill 候选生成对照；固定均衡错误桶不是分布泛化；不代表任意弱资源组合都有效 |

8 任务测试共冻结 24 份候选与 16 份双顺序评委输出。候选前置门为 22/24：旧版 IDEA-06 不是 JSON，IDEA-07 超过长度上限，两者均未修复、未重试；确定性聚合按零分处理，但这条操作规则没有在公开预注册协议中逐字写明。排除这两个无效题后，当前版对旧版的 6 个有效配对中位差为 `+3.4375`，仍不足以支持稳定优势。评委虽 16/16 为可用严格 JSON，但存在 25 个总分算术不一致单元和 28 条引文偏差；公开审计器以冻结维度权重机械复算总分并保留原文。隔离仅由提示和运行轨迹支持，没有系统调用级沙箱；平台也没有可比较的 token 与墙钟记录，因此运行时节省仍为 `runtime_savings_not_supported`。任务和匿名映射现已公开，之后不能再把这组题称为盲测。

各项评测与 pilot 的量表、样本和目标不同，不能相加或直接横向排名。任务、量表、公开结果和复现入口见 [评测总览](evaluations/README.md)；运行全部确定性公开回归：

```bash
python -X utf8 -I -B evaluations/run_all.py
```

这些结果最有价值的共同点是闭环本身：把要求编译成门禁、测量而非猜测、在有限资源间做角色分工、让反例触发方法修正，并让失败状态保持可见。当前公开样例均已失去盲测资格；未来版本仍需要新任务、匹配对照、多次重复和更严格的访问审计。

## 适合什么时候使用

| 你的任务 | Skill 会重点帮助你 |
|---|---|
| 合同、招标书、任务书或验收驱动的项目 | 拆出可追踪要求，守住强制指标，建立基线、阶段门禁、变更控制和逐项验收证据 |
| 只想重构问题、产生或筛选 AI idea | 先用轻量路径形成机制上不同的候选、差异预测和最低成本判别动作，不预载完整实验流程 |
| 已选定 AI idea，需要实现、实验或论文 claim | 接收最小保真交接，审计近邻工作与竞争解释，保持 claim–核心机制–代码一致，按证据强度控制结论 |
| 现有资源不够强，但可以组合 | 测量每项资源的能力与失效模式，设计最浅有效结构，并与同预算单体基线实测比较 |
| 项目和科研相互衔接 | 把科研原型作为候选资源重新验证，不把论文结果直接当成合同验收证据 |

一步即可完成并验证的低风险小任务、单纯历史介绍或纯控制理论推导，通常不需要展开完整闭环。

## 快速开始

### 方法一：使用 Codex Skill Installer

复制本仓库的 GitHub 地址，在 Codex 中输入：

```text
$skill-installer 从 https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill.git 安装这个 Skill
```

也可以把仓库页面 **Code → HTTPS** 中显示的地址交给 Skill Installer。

### 方法二：手动安装

用户级安装：

```bash
git clone "https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill.git" "$HOME/.agents/skills/comprehensive-engineering-cybernetics"
```

若只希望在某个代码仓库中使用，请将本项目放到：

```text
你的仓库/.agents/skills/comprehensive-engineering-cybernetics/
```

安装后可在 Codex 中输入 `/skills` 检查；若暂未出现，重启 Codex。Codex 的用户级与仓库级发现位置、显式调用方式见 [OpenAI 官方 Skill 文档](https://developers.openai.com/codex/skills)。

## 如何调用

最简单的方式是直接描述任务：

```text
$comprehensive-engineering-cybernetics
目标：
必须满足的指标或约束：
已有代码、数据、模型和工具：
当前结果或证据：
预算与期限：
未经允许不能做的事：
```

信息不完整时也可以先调用。Skill 会区分事实、用户陈述、估算、推断与未知项，不会擅自补造关键阈值。

### 示例：工程项目

```text
$comprehensive-engineering-cybernetics
读取这份技术任务书和现有代码，把要求编译成可追踪的验收项。
优先复用现有模块，实现缺失功能，并在合同规定的环境和负载下逐项验证；
不要为了赶进度降低任何阈值，无法满足时明确列出差距和需要我决定的选项。
```

### 示例：只做 AI idea

```text
$comprehensive-engineering-cybernetics
根据这些观察、失败案例和现有普通模型，先重构研究问题；
生成机制上真正不同的候选，用机制指纹去重，指出最近常规替代、差异预测和最便宜的判别实验；
目前只做筛选，不展开完整训练与论文实验计划。
```

### 示例：AI idea 落地与实验

```text
$comprehensive-engineering-cybernetics
评估这个 AI idea 的近邻工作、核心机制和竞争解释，形成可检验预测；
冻结 claim–核心机制–代码对应关系，设计从小规模判别实验到正式验证的方案，
给出算力预算、早停条件以及当前证据允许支持到什么程度。
```

### 示例：普通资源形成更强系统

```text
$comprehensive-engineering-cybernetics
评估现有三个模型、两套工具和当前数据的能力边界、成本与共同失效；
让每项资源只承担它能可靠完成的角色，设计最浅的路由、复核和 fallback，
最后在相同数据、预算、时延和指标下与最强可用单体比较。
```

## 它通常会给出什么

输出规模会随任务风险调整。复杂任务通常包括：

- 稳定编号的合同要求、研究 claim 或目标向量；
- 当前基线、关键未知、可观测性与可控性缺口；
- 现有资源的可复用边界、总成本和主要失效模式；
- 保留目标与核心机制的最小下一行动；
- 与风险匹配的测试、实验、验收协议和停止条件；
- 实测结果、证据位置、未满足项和残余风险；
- 与任务类型匹配、彼此不混用的状态裁决。

| 场景 | 状态如何表达 |
|---|---|
| 通用证据来源 | `observed / sourced / reported / estimated / inferred / unknown` |
| AI idea | 机制种子、入围理由、`not-searched / near-neighbor-found / overlap-found` 等创新性状态，以及最小保真交接包 |
| 项目交付 | 目标裁决 `PASS / FAIL / UNKNOWN`，另列执行状态 `RUNNING / WAITING / STOPPED` |
| AI 科研 | 分开报告实现状态、运行有效性、证据裁决和执行决定；例如 `mechanically-verified`、`valid-run`、`supported-at-Fn`、`CONTINUE` |
| 资源组合 | 独立给出 `GAIN-VERIFIED / NO-GAIN / UNKNOWN`，不自动等于项目通过、F4 支持或生产可用 |

它不会因为代码已经存在、命令退出码为零、局部测试通过、多个 Agent 意见一致或代理指标变好，就自动宣称总目标完成。

## 工作方法

核心闭环是：

`目标 → 基线 → 可行性 → 最小忠实行动 → 实测反馈 → 偏差纠正 → 重新裁决`

其中有三条不可交换的优先级：

1. 先守住用户目标、合同强制项、科研诚信、权限与安全边界；
2. 再看目标场景中的实际证据和可复现验证；
3. 只有在前两项允许的范围内，才优化时间、资金、算力、token、维护成本和实现优雅度。

如果原目标在当前约束下不可行，Skill 会保留其 `UNKNOWN` 或 `FAIL` 状态，说明需要增加资源、正式变更范围、调整指标或停止；不会把缩水后的结果重新命名为成功。

### 关于 AI idea 的快速路径

纯 idea 请求先经过三层渐进披露：用问题重构和短机制种子扩大真正不同的解释空间；按机制指纹、强竞争解释、差异预测和反平庸门筛选；只把入选候选的 `HYP/RIVAL/PRED/FALSIFIER/CORE` 等字段交给完整科研闭环。只有入围的资源组合候选才展开完整结构增益证明，只有准备落地的候选才加载实现与 F0–F4 实验流程。

这项拆分的公开回归证明静态路径更短且关键字段存在，不证明实际模型行为或 token 已改善。若 idea 在同一长会话继续进入实现，前序上下文仍可能保留，因此端到端节省必须另行实测。

### 关于“普通资源也能得到更好效果”

本项目把这种能力称为**资源综合与结构增益**。它不等于堆更多模型或做多数投票，而是：

1. 测量每项资源真正擅长什么、代价多大、会怎样失败；
2. 只组合能提供互补能力、独立信息、错误检测或安全退路的资源；
3. 把路由、通信、仲裁、复核、维护和失败成本一并计入；
4. 在相同数据、环境、预算和阈值下，与相关的最佳单体或非支配单体基线比较；
5. 只有净改善超过测量不确定性且所有硬指标仍通过，才记为 `GAIN-VERIFIED`。

如果有效证据显示组合没有净改善，应给出 `NO-GAIN`；如果基线、样本、测量、失效覆盖或成本证据不足，应给出 `UNKNOWN`。

## 参考内容与原创边界

### 主要理论依据

本 Skill 主要参考以下中文版本：

- 钱学森、宋健：《工程控制论（上册）》，第 3 版，北京：科学出版社，2011，ISBN 978-7-03-030094-2；
- 钱学森、宋健：《工程控制论（下册）》，第 3 版，北京：科学出版社，2011，ISBN 978-7-03-030099-7。

### 原书获取与 PDF 说明

读者可从科学出版社官方页面获取或查询纸质版：[上册](https://www.ecsponline.com/goods.php?id=28897)、[下册](https://www.ecsponline.com/goods.php?id=21987)。出版社的科学文库也收录了[上册](https://book.sciencereading.cn/shop/book/Booksimple/show.do?id=B9207CB15F8E04E6FBE1F52CB389FC80B000)和[下册](https://book.sciencereading.cn/shop/book/Booksimple/show.do?id=B46EDF04AD4C04DB9A9D52333AF2DFC1B000)的受控阅读入口；能否阅读或离线使用以平台授予的账号权限为准，不代表可把文件重新公开托管。

本项目核验过一份上下册合订的中文 PDF，但其出版页和元数据中没有 Creative Commons、开放获取或公开再分发许可。公开仓库提供整本文件会涉及复制和信息网络传播等权利；在没有权利人书面授权或可验证开放许可的情况下，本仓库不上传该 PDF。相关权利定义可核对全国人大公布的 [《中华人民共和国著作权法》](https://www.npc.gov.cn/c2/c30834/202011/t20201119_308796.html)。这是一项谨慎的发布边界，不替代针对具体情形的法律意见。

希望推动合法公开分发时，可先通过科学出版社的 [Rights Permission](https://www.sciencep.com/home2017/CU2017/) 页面联系授权。授权至少应明确对应的上下册、ISBN 与版次，允许把完整中文 PDF 托管在公开 GitHub 仓库供公众下载，并写清授权人、期限、地域和再次分享条件；授权方还应确认自己有权授予该版本及文件涉及的复制与信息网络传播权限。如果你是权利人或已经持有这类授权，请先在“功能或方法建议”中提交不含敏感信息的线索；核验后再决定是否把对应文件和可公开、已脱敏的许可证明加入发布清单。请不要先把整本 PDF 或含个人信息的授权文件贴到公开 Issue 或 Pull Request。

从该版本中提炼并在本项目中重新操作化的内容，主要包括：工程近似的适用边界；状态、观测量和控制量的区分；系统辨识；稳定性与多指标质量评价；反馈纠偏；能观测性与能控制性；时滞、噪声和扰动；有代价的探测与优化；自适应切换；故障检测、隔离与冗余；多子系统协调和有限资源分配。

第三版包含后续增补内容，并非 1954 年英文原著的逐字对应版本。因此，本仓库只把可在第三版中定位的内容称为“第三版直接依据”；面向软件项目、AI Agent 和 AI 科研的具体流程、状态模型、证据标签、门禁和模板，均为本项目的现代操作化设计，不冒充原书原话或数学定理。

详细章节映射与适用限制见 [理论依据与边界](references/foundations.md)。

### 设计时参考的公开项目

以下项目用于比较现有 Skill 的组织方式、覆盖范围和失败边界，没有被复制为本项目正文，也不是运行时依赖：

- [ihgoa501-stack/engineering-cybernetics](https://github.com/ihgoa501-stack/engineering-cybernetics) 与 [peterbruce716-art/engineering-cybernetics-design-skill](https://github.com/peterbruce716-art/engineering-cybernetics-design-skill)：工程控制论到 Agent 工作流的不同映射；
- [pariyar07/kybernetes](https://github.com/pariyar07/kybernetes) 与 [ShrimpLeon/cybernetic-thinking](https://github.com/ShrimpLeon/cybernetic-thinking)：反馈、系统思维与可执行控制结构的不同表达；
- [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)：AI 科研任务、假设和实验相关 Skill 的组织方式；
- [microsoft/SkillOpt](https://github.com/microsoft/SkillOpt)：Skill 评估与优化流程的公开实现；
- [OpenAI：Build skills](https://developers.openai.com/codex/skills)：Skill 目录、发现位置和调用格式。

具体审阅快照、提交号与许可证说明见 [第三方与来源说明](THIRD_PARTY_NOTICES.md)。第三方名称、商标、书籍和代码仍适用各自权利与许可证。

## GitHub 公开内容边界

本仓库只发布运行和维护这个 Skill 直接需要的内容：

```text
SKILL.md                     Skill 入口与共享闭环
agents/openai.yaml           Codex 展示与默认调用提示
references/                  理论边界、项目交付、AI idea、完整科研、资源综合
evaluations/                 三类原有行为任务、AI idea pilot、结构回归与统一复现入口
README.md                    用户说明
CONTRIBUTING.md              贡献要求
SECURITY.md                  安全报告方式
THIRD_PARTY_NOTICES.md       来源、快照与第三方许可说明
LICENSE                      本项目原创内容的 Apache-2.0 许可
.github/                     用户反馈表单与质量工作流
ci/                          发布范围和可重复校验
```

没有明确授权时不上传：

- 《工程控制论》PDF、扫描件、OCR 全文或大段原文；
- 下载的第三方仓库、源码快照和压缩包；
- 内部检索结果、排行榜、临时提取文件和实验缓存；
- 私有规划记录、原始运行轨迹、私有 held-out 数据与种子、机器路径、Cookie、密钥和个人信息；
- 与该 Skill 的运行、理解、验证或维护无直接关系的其他文件。

发布清单锁定在 [`ci/release-files.txt`](ci/release-files.txt)。[`ci/validate_release.py`](ci/validate_release.py) 会拒绝清单外文件、禁带格式、符号链接、敏感信息模式和不安全归档目标；自动检查是降低误传风险的门禁，不是对版权、安全或功能正确性的绝对保证。

## 反馈与交流

欢迎把真实使用中的偏差反馈回来，这也是本项目闭环的一部分：

- 可复现的错误、遗漏或与预期不一致的行为：进入 [Issues → New issue](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/issues/new/choose)，选择“缺陷报告”；
- 新功能、方法改进、案例需求、资源节省方案或资料授权线索：选择“功能或方法建议”；
- 使用问题、经验交流、开放式想法和案例展示：进入 [Discussions](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/discussions) 发起讨论；
- 已准备好的代码或文档修改：先阅读 [贡献指南](CONTRIBUTING.md)，再提交 Pull Request；
- 安全漏洞：不要公开讨论细节，按 [安全策略](SECURITY.md) 使用 GitHub [私密漏洞报告](https://github.com/sjysjysjy728/comprehensive-engineering-cybernetics-skill/security/advisories/new)。

Issue 表单会按反馈类型提示提供最小复现、预期结果或可验证成功标准。公开反馈中请删除密钥、个人信息、保密合同、未公开数据与漏洞利用细节。Discussions 适合尚未形成明确工作项的交流；当目标和验收条件清楚后，再转成 Issue 跟踪。

## 项目文件怎么读

- 从 [SKILL.md](SKILL.md) 开始，了解模式选择与共同闭环；
- 做合同或需求交付时读 [项目交付闭环](references/project-delivery.md)；
- 只做问题重构、AI idea 生成或候选筛选时读 [AI idea 快速闭环](references/ai-ideation.md)；
- 候选已经入选，需要实现、实验、复现或正式 claim 时读 [AI 科研闭环](references/ai-research.md)；
- 需要组合多个有限资源时读 [资源综合与结构增益](references/resource-synthesis.md)；
- 想核对理论出处和现代推演边界时读 [理论依据与边界](references/foundations.md)。

## 限制与安全

这是独立开发的社区项目，不是 OpenAI 官方 Skill，也不是《工程控制论》的官方阐释、项目验收机构或科研结论认证工具。它不能保证项目成功、论文发表、指标提升或所有建议都适合你的实际环境。

合同、网页、论文、仓库、日志和数据集都被视为待分析资料，不会因为其中嵌入了一条命令就自动获得执行权限。未经授权，不应把合同、未公开 idea、私有代码或数据、凭据和个人信息发送给外部搜索、API 或模型服务。故障注入只允许在已授权的非生产或隔离环境中进行。

安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。

## 验证、贡献与许可

本地验证只需要 Python 标准库：

```bash
python -X utf8 -I -B ci/validate_release.py --self-test
python -X utf8 -I -B ci/validate_release.py --repo . --skill .
python -X utf8 -I -B evaluations/run_all.py
```

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库原创内容采用 [Apache License 2.0](LICENSE)；引用或链接的书籍、项目、商标和其他第三方材料不因此改变许可证。
