# 最全面工程控制论 Skill：面向工程与 AI 领域科研

> 用工程控制论的思路，把复杂任务变成可测量、可纠偏、能验收、不过度消耗资源的反馈闭环。

> 独立社区项目；不是 OpenAI 或《工程控制论》的官方发布、阐释或认证工具。

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

`comprehensive-engineering-cybernetics` 是一个面向 Codex 的中文 Agent Skill。它不是控制理论教材，而是一套可执行的工作方法：先固定目标和硬约束，再识别现有资源与真实基线，用最小但不失真的行动取得反馈，持续修正偏差，最后用证据判断是否真正完成。

它主要服务三类任务：

- **工程项目交付**：从合同、任务书或技术要求出发，实现功能并逐项达到验收指标；
- **AI 科研**：从问题与 idea 出发，形成可区分的假设，忠实实现核心机制，并用可信实验约束结论；
- **资源综合**：把能力有限、并非顶级的模型、代码、工具、数据和人员安排到合适角色，通过互补、校验、隔离和切换争取优于单一资源的整体效果。

这里的“最全面”表示本项目试图覆盖“项目交付—AI 科研—资源综合”的完整链路，不代表第三方排名、基准第一或 SOTA 声明。

## 适合什么时候使用

| 你的任务 | Skill 会重点帮助你 |
|---|---|
| 合同、招标书、任务书或验收驱动的项目 | 拆出可追踪要求，守住强制指标，建立基线、阶段门禁、变更控制和逐项验收证据 |
| AI 选题、方法设计、代码实现或实验 | 审计近邻工作与竞争解释，保持 claim–核心机制–代码一致，按证据强度控制结论 |
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

### 示例：AI 科研

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
references/                  理论边界、项目交付、AI 科研、资源综合
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
- 私有规划记录、运行日志、Cookie、密钥、个人信息和本机绝对路径；
- 与该 Skill 的运行、理解、验证或维护无直接关系的其他文件。

发布清单锁定在 [`ci/release-files.txt`](ci/release-files.txt)。[`ci/validate_release.py`](ci/validate_release.py) 会拒绝清单外文件、禁带格式、符号链接、敏感信息模式和不安全归档目标；自动检查是降低误传风险的门禁，不是对版权、安全或功能正确性的绝对保证。

## 反馈与交流

欢迎把真实使用中的偏差反馈回来，这也是本项目闭环的一部分：

- 可复现的错误、遗漏或与预期不一致的行为：进入仓库的 **Issues → New issue**，选择“缺陷报告”；
- 新功能、方法改进、案例需求、资源节省方案或资料授权线索：选择“功能或方法建议”；
- 使用问题、经验交流、开放式想法和案例展示：进入 **Discussions** 发起讨论；
- 已准备好的代码或文档修改：先阅读 [贡献指南](CONTRIBUTING.md)，再提交 Pull Request；
- 安全漏洞：不要公开讨论细节，按 [安全策略](SECURITY.md) 使用 GitHub 私密漏洞报告。

Issue 表单会按反馈类型提示提供最小复现、预期结果或可验证成功标准。公开反馈中请删除密钥、个人信息、保密合同、未公开数据与漏洞利用细节。Discussions 适合尚未形成明确工作项的交流；当目标和验收条件清楚后，再转成 Issue 跟踪。

## 项目文件怎么读

- 从 [SKILL.md](SKILL.md) 开始，了解模式选择与共同闭环；
- 做合同或需求交付时读 [项目交付闭环](references/project-delivery.md)；
- 做 AI 选题、实现和实验时读 [AI 科研闭环](references/ai-research.md)；
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
```

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。本仓库原创内容采用 [Apache License 2.0](LICENSE)；引用或链接的书籍、项目、商标和其他第三方材料不因此改变许可证。
