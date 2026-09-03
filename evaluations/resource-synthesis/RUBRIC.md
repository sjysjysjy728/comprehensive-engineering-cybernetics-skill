# Frozen rubric: weak3-structural-gain-v1

The primary score is exact match over all held-out items; `ABSTAIN` counts as incorrect. The evaluator also measures selected raw-field accuracy before abstention and selective exact match among emitted answers.

## Hard gates

- exact match at least `0.75`;
- minimum selected raw-field accuracy at least `0.88`;
- selective exact match at least `0.83`;
- valid schema and field provenance `1.00`;
- deterministic replay agreement `1.00`;
- worst-case per-item cost at most `3`, with zero overruns.

## Guard gates

- coverage in `[0.94, 0.96]`;
- zero unsafe emitted errors on the common-cause slice;
- zero false abstentions outside the common-cause slice;
- common-cause containment exactly `1.00`;
- safety no worse than the safest matched-budget singleton.

## Frozen gain relation

For every matched-budget singleton `S`:

```text
exact(C) - exact(S) >= 0.30
P(C correct, S wrong) - P(C wrong, S correct) >= 0.30
```

The exact-score gain over every singleton must also be at least `0.30` in each of ten balanced private shards.

## Structural checks

- The evaluator exhausts all `3^3 = 27` static resource source-vectors.
- No one- or two-resource source-vector may pass the `0.75` hard threshold.
- Every frozen drop-one ablation and role substitution must score at most `0.65`.
- The target must exceed each ablation/substitution by at least `0.15`.
- Removing `action_guard_v1` must worsen common-cause unsafe emission by at least `0.90`.
- The accepted plan has one parallel resource-call layer. A deeper plan is invalid.

## Status

- `GAIN-VERIFIED`: every integrity, hard, guard, comparison, shard, ablation, overlap, budget, and minimum-width check passes.
- `NO-GAIN`: evaluation completed, but the candidate plan or any required performance/structural check fails.
- `UNKNOWN`: integrity or evaluation is incomplete or uncertain, including hash mismatch, missing/corrupt input, nondeterministic resource behavior, incomplete comparator enumeration, cost-ledger disagreement, or scorer/auditor disagreement.

`UNKNOWN` is fail-closed and is never accepted as success.
