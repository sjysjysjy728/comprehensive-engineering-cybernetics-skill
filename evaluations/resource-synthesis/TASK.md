# Frozen task: weak3-structural-gain-v1

Design the shallowest valid composition of three deterministic, limited resources for an incident decision task. For every opaque `case_id`, the system must emit either a three-field decision `(site, mode, action)` or `ABSTAIN`.

The available resources are:

| Resource | Primary role | Cost per call |
|---|---|---:|
| `site_v1` | locate the affected site | 1 credit |
| `mode_v1` | identify the failure mode | 1 credit |
| `action_guard_v1` | choose an action and raise a common-cause alarm | 1 credit |

The fixed per-item budget is 3 credits. Calls are deterministic and idempotent. They may run in one parallel layer; adaptive or sequential calls are forbidden.

The original candidate received a 400-case public development fixture and a standard-library profiler with which to characterize the resources. It had to submit exactly two files:

1. `plan.json`: a declarative `weak3-plan-v1` plan accepted by the grammar below.
2. `REPORT.md`: at most 500 words describing the resource roles, why the composition is shallow, expected residual failures, and budget.

Executable candidate code was forbidden.

## Plan grammar

```json
{
  "schema_version": "weak3-plan-v1",
  "calls": [
    {"id": "unique-id", "resource": "site_v1|mode_v1|action_guard_v1"}
  ],
  "fields": {
    "site":   {"call": "unique-id", "field": "site"},
    "mode":   {"call": "unique-id", "field": "mode"},
    "action": {"call": "unique-id", "field": "action"}
  },
  "abstain_if": {"op": "or_all_alarms"}
}
```

Exactly three calls are required, so the target and all matched-budget comparators spend 3 credits. Each output must take the same-named field from one declared call. Constants, transforms, cross-field copying, branching on IDs or reply values, custom code, omitted alarms, and unknown keys are invalid.

The private evaluation used 2,000 fixed, balanced held-out cases. The comparison relation, thresholds, ablations, substitutions, status rules, and evaluator were frozen before the candidate plan was evaluated. The original seed and reveal are excluded from this package. `evaluate.py` derives a separate public regression fixture from a fixed label; it reproduces the balanced structural scores but cannot re-establish the historical held-out condition.
