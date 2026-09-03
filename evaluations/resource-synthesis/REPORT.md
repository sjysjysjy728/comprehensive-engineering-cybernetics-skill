# weak3 structural-gain plan

> 这是独立评分前冻结的候选报告；其中 `UNKNOWN` 是揭示测试种子之前的正确状态，不是发布后的最终裁决。

Status before independent scoring: **UNKNOWN**. The candidate is frozen from public development evidence; it does not claim held-out `GAIN-VERIFIED`.

## Roles and observed failures

The supplied standard-library profiler evaluated 400 development cases and all 27 static field-source vectors. `site_v1` is the site specialist: field accuracies `(site, mode, action) = (0.90, 0.65, 0.65)`. `mode_v1` is the mode specialist at `(0.65, 0.90, 0.65)`. `action_guard_v1` is the action specialist and common-cause detector at `(0.65, 0.65, 0.90)`. Their singleton raw exact scores are `0.40`, `0.40`, and `0.35`, respectively. Thus each resource is assigned only its strongest observed role.

The selected source vector is `(site_v1, mode_v1, action_guard_v1)`. It is the profiler's unique best vector, with development raw exact `0.80`; the best vectors using only one and two distinct resources reach only `0.40` and `0.60`. Expected residual failures are the non-common buckets where any selected specialist field is wrong. The common-cause bucket is a correlated three-field failure, not independent redundancy: `action_guard_v1` alarms there, and `or_all_alarms` converts it to `ABSTAIN`. On the balanced development construction this implies expected coverage `0.95`, emitted exact `0.80`, and selective exact `0.80/0.95 = 0.8421`; abstention remains incorrect for primary exact scoring. Residual risks include generator shift, correlated errors outside the alarmed slice, and any private integrity or replay disagreement.

## Depth, budget, and comparison boundary

All three deterministic calls run in one parallel layer; there is no routing, retry, adaptation, voting, transform, or cross-field copy. This is the shallowest grammar-valid composition and costs exactly `3` credits per item (`1 + 1 + 1`), with worst-case cost `3` and no budget-dependent path. The named matched-budget singleton comparators remain unchanged. More calls are not treated as gain: gain is the frozen exact, paired, per-shard, ablation, substitution, containment, and guard comparison at equal cost.

Held-out gain remains unverified because the 2,000 private cases, hashes, comparator enumeration, auditor agreement, and frozen structural checks are unavailable here. Only independent scoring can change status from `UNKNOWN` to `GAIN-VERIFIED` or `NO-GAIN`.
