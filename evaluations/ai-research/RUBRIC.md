# CEC-MiniResearch-1 评测量规

机器门禁与主观 idea 质量分开裁决。主观高分不能挽救任何机器门禁失败。

## 机器门禁

历史私有评分器给出 15 个 fail-closed 门禁：

| 门禁 | 要求 |
|---|---|
| Submission size | UTF-8 单文件不超过 64 KiB |
| Schema / traceability / evidence | 恰好 3 个 Idea Card，结构、追踪、证据上限均有效 |
| Frozen runner | 候选运行器和 DSL helper 与冻结副本哈希一致 |
| Runtime | 两次执行均在 5 秒内完成 |
| Prediction integrity | 每个 ID 恰好一个有限预测，ID 完全一致 |
| Canonical replay | 预测和审计与标准 DSL 回放误差不超过 `1e-6` |
| Reproducibility | 重复执行逐字节一致 |
| Row / ID invariance | 打乱行并重命名 ID 后，对齐预测变化不超过 `1e-9` |
| Public honesty | 报告的公开主模型、rival RMSE 和 lift 与重算误差不超过 `1e-6` |
| Public falsification | 公开相对 RMSE lift 至少 0.15 |
| Held-out factorial | NRMSE 至多 0.25，训练均值基线改善至少 0.60 |
| Held-out additive ablation | 相对加性 rival 的 lift 至少 0.20 |
| Held-out shadow | NRMSE 至多 0.30，训练均值基线改善至少 0.60 |
| Held-out boundary | MAE 至多 0.35 |
| Declared direction | 机制项方向与预声明一致 |

指标使用总体标准差：

```text
RMSE = sqrt(mean((prediction - target)^2))
NRMSE = RMSE / population_sd(target)
baseline improvement = 1 - RMSE_model / RMSE_training_mean
additive-rival lift = 1 - RMSE_primary / RMSE_additive_rival
```

结构层级规则是本测试闭环修复后的新增门：当 claim 表述交互、乘积、阈值或高阶项在低阶效应之外提供增量解释时，主模型与 rival 必须保留相同的必要低阶主效应，形成嵌套比较；否则只能报告非嵌套预测比较。

## 双顺序盲评

判官只看到规范化后的 Idea Card、选择理由、假设、rival、实验逻辑和证据上限；不看到机器指标、条件标签、文件名或运行元数据。

| 维度 | 权重 |
|---|---:|
| 三个 idea 的机制洞察与区分度 | 30 |
| rival 公平性与证伪锐度 | 25 |
| held-out 与消融逻辑 | 20 |
| 经济性及 claim-to-model 一致性 | 15 |
| 认识论校准 | 10 |

每个维度按 0–5 分评分，再换算为 100 分加权总分。候选位置在两个新上下文中交换。只有同一底层候选在两个顺序都被偏好，且平均分差至少为 5/100，才能获胜；否则为平局。单候选跨顺序分数移动超过 8/100 时标记为位置敏感。

判官自报总分必须与维度分按上述权重重算一致；不一致的判决 fail closed，不进入聚合。

## 解释原则

- 机器门禁通过证明候选在固定合成任务中的运行、结构与预测证据有效；
- 盲评比较 idea、rival 和 claim-to-model 的质量，不替代机器验证；
- token、工具调用和模型复杂度分别报告，不把较少模型项等同于端到端资源节省；
- 定向修复使用了初测反馈，属于 benchmark-informed regression，不是新的独立验证。
