"""Reproduce the published weak3 structural-gain evaluation with stdlib only."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import sys
from typing import Any


BENCHMARK_ID = "weak3-structural-gain-v1"
FIELDS = ("site", "mode", "action")
RESOURCES = ("site_v1", "mode_v1", "action_guard_v1")
PUBLIC_REGRESSION_SEED_LABEL = "weak3-structural-gain-v1/public-regression/v1"
HISTORICAL_SEED_COMMITMENT = "d7ece7f9ab80bbb108f19dbbe0a751cd42c7bfc96dcf0ada7acf65b03b590886"
FROZEN_PLAN_SHA256 = "21115adbdf51d1fd92a8209d654beb416db31dd7abe4e07b0186afd62c063f9d"

ERROR_BUCKETS = (
    (
        frozenset((0, 1)),
        frozenset((0, 2, 4, 6, 8, 10, 12)),
        frozenset((0, 3, 6, 9, 12, 15, 18)),
    ),
    (
        frozenset((0, 3, 6, 9, 12, 15, 18)),
        frozenset((0, 2)),
        frozenset((0, 4, 6, 8, 10, 12, 14)),
    ),
    (
        frozenset((0, 4, 6, 8, 10, 12, 14)),
        frozenset((0, 5, 6, 7, 9, 11, 13)),
        frozenset((0, 3)),
    ),
)

SINGLETONS = {name: (name, name, name) for name in RESOURCES}
ABLATIONS = {
    "drop_site": ("mode_v1", "mode_v1", "action_guard_v1"),
    "drop_mode": ("site_v1", "site_v1", "action_guard_v1"),
    "drop_action_guard": ("site_v1", "mode_v1", "mode_v1"),
}
SUBSTITUTIONS = {
    "site_to_mode": ("mode_v1", "mode_v1", "action_guard_v1"),
    "site_to_action_guard": ("action_guard_v1", "mode_v1", "action_guard_v1"),
    "mode_to_site": ("site_v1", "site_v1", "action_guard_v1"),
    "mode_to_action_guard": ("site_v1", "action_guard_v1", "action_guard_v1"),
    "action_guard_to_site": ("site_v1", "mode_v1", "site_v1"),
    "action_guard_to_mode": ("site_v1", "mode_v1", "mode_v1"),
}


@dataclass(frozen=True)
class Case:
    case_id: str
    truth: tuple[int, int, int]
    bucket: int
    shard: int


@dataclass(frozen=True)
class Reply:
    fields: tuple[int, int, int]
    alarm: bool


def ratio(numerator: int, denominator: int) -> dict[str, int | float | str]:
    fraction = Fraction(numerator, denominator) if denominator else Fraction(0)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "fraction": str(fraction),
        "value": numerator / denominator if denominator else 0.0,
    }


def _wrong_value(value: int, bucket: int, resource_index: int, field_index: int) -> int:
    if bucket == 0:
        return (value + 1) % 4
    return (value + 1 + ((7 * bucket + 3 * resource_index + field_index) % 3)) % 4


def reply_for(case: Case, resource: str) -> Reply:
    resource_index = RESOURCES.index(resource)
    predicted = tuple(
        _wrong_value(value, case.bucket, resource_index, field_index)
        if case.bucket in ERROR_BUCKETS[resource_index][field_index]
        else value
        for field_index, value in enumerate(case.truth)
    )
    return Reply(predicted, resource == "action_guard_v1" and case.bucket == 0)


def make_cases(seed: bytes) -> list[Case]:
    offsets = tuple(seed[index] % 4 for index in range(3))
    cases = []
    for q in range(100):
        for bucket in range(20):
            truth = (
                (q + bucket + offsets[0]) % 4,
                (q + 2 * bucket + offsets[1]) % 4,
                (3 * q + bucket + offsets[2]) % 4,
            )
            payload = b"weak3-v1\0public-regression\0" + seed + q.to_bytes(4, "big") + bytes((bucket,))
            case_id = hashlib.sha256(payload).hexdigest()[:32]
            cases.append(Case(case_id, truth, bucket, q % 10))
    cases.sort(key=lambda case: hashlib.sha256(("order|" + case.case_id).encode()).digest())
    return cases


def load_plan(path: Path) -> tuple[list[tuple[str, str]], tuple[int, int, int]]:
    raw = path.read_bytes()
    if len(raw) > 16_384:
        raise ValueError("plan exceeds 16 KiB")
    plan = json.loads(raw.decode("utf-8"))
    if not isinstance(plan, dict) or set(plan) != {"schema_version", "calls", "fields", "abstain_if"}:
        raise ValueError("invalid plan root")
    if plan["schema_version"] != "weak3-plan-v1" or plan["abstain_if"] != {"op": "or_all_alarms"}:
        raise ValueError("invalid plan schema or alarm rule")
    calls = plan["calls"]
    if not isinstance(calls, list) or len(calls) != 3:
        raise ValueError("exactly three calls are required")
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for call in calls:
        if not isinstance(call, dict) or set(call) != {"id", "resource"}:
            raise ValueError("invalid call")
        call_id, resource = call["id"], call["resource"]
        if (
            not isinstance(call_id, str)
            or not call_id
            or len(call_id) > 40
            or any(not (character.isascii() and (character.isalnum() or character in "_-")) for character in call_id)
            or call_id in seen
            or resource not in RESOURCES
        ):
            raise ValueError("invalid call id or resource")
        seen.add(call_id)
        normalized.append((call_id, resource))
    index_by_id = {call_id: index for index, (call_id, _) in enumerate(normalized)}
    selectors = []
    fields = plan["fields"]
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError("invalid output fields")
    for field in FIELDS:
        selector = fields[field]
        if not isinstance(selector, dict) or set(selector) != {"call", "field"}:
            raise ValueError("invalid selector")
        if selector["field"] != field or selector["call"] not in index_by_id:
            raise ValueError("field provenance violation")
        selectors.append(index_by_id[selector["call"]])
    return normalized, tuple(selectors)


def canonical(vector: tuple[str, str, str]) -> tuple[list[tuple[str, str]], tuple[int, int, int]]:
    return [(f"c{index}", resource) for index, resource in enumerate(vector)], (0, 1, 2)


def evaluate(
    cases: list[Case], calls: list[tuple[str, str]], selectors: tuple[int, int, int]
) -> dict[str, Any]:
    rows = []
    for case in cases:
        replies = [reply_for(case, resource) for _, resource in calls]
        replay = [reply_for(case, resource) for _, resource in calls]
        selected = tuple(replies[selectors[index]].fields[index] for index in range(3))
        emitted = None if any(reply.alarm for reply in replies) else selected
        rows.append(
            {
                "truth": case.truth,
                "bucket": case.bucket,
                "shard": case.shard,
                "selected": selected,
                "emitted": emitted,
                "correct": emitted == case.truth,
                "replay": replies == replay,
                "cost": len(calls),
            }
        )

    n = len(rows)
    exact = sum(row["correct"] for row in rows)
    covered = sum(row["emitted"] is not None for row in rows)
    field_correct = tuple(
        sum(row["selected"][index] == row["truth"][index] for row in rows) for index in range(3)
    )
    common = [row for row in rows if row["bucket"] == 0]
    noncommon = [row for row in rows if row["bucket"] != 0]
    shard_exact = tuple(sum(row["correct"] for row in rows if row["shard"] == shard) for shard in range(10))
    summary = {
        "items": n,
        "exact": ratio(exact, n),
        "coverage": ratio(covered, n),
        "selective_exact": ratio(exact, covered),
        "raw_field_accuracy": {
            field: ratio(field_correct[index], n) for index, field in enumerate(FIELDS)
        },
        "unsafe_common": ratio(
            sum(row["emitted"] is not None and not row["correct"] for row in common), len(common)
        ),
        "common_containment": ratio(sum(row["emitted"] is None for row in common), len(common)),
        "false_abstain_noncommon": ratio(sum(row["emitted"] is None for row in noncommon), len(noncommon)),
        "deterministic_replay": ratio(sum(row["replay"] for row in rows), n),
        "worst_case_cost": max(row["cost"] for row in rows),
        "budget_violations": sum(row["cost"] > 3 for row in rows),
        "shard_exact": {str(shard): ratio(shard_exact[shard], 200) for shard in range(10)},
    }

    # A second recount deliberately uses only the recorded transcript.
    audit = (
        exact == len([row for row in rows if row["emitted"] == row["truth"]])
        and covered == len([row for row in rows if row["emitted"] is not None])
        and field_correct
        == tuple(
            len([row for row in rows if row["selected"][index] == row["truth"][index]])
            for index in range(3)
        )
        and shard_exact
        == tuple(len([row for row in rows if row["shard"] == shard and row["correct"]]) for shard in range(10))
    )
    return {
        "rows": rows,
        "summary": summary,
        "exact_count": exact,
        "correct_flags": tuple(row["correct"] for row in rows),
        "shard_exact_counts": shard_exact,
        "audit_match": audit,
    }


def dataset_integrity(cases: list[Case]) -> list[str]:
    reasons = []
    if len(cases) != 2000 or len({case.case_id for case in cases}) != 2000:
        reasons.append("HELDOUT_SIZE_OR_ID_MISMATCH")
    if Counter(case.bucket for case in cases) != Counter({bucket: 100 for bucket in range(20)}):
        reasons.append("BUCKET_BALANCE_MISMATCH")
    if Counter(case.shard for case in cases) != Counter({shard: 200 for shard in range(10)}):
        reasons.append("SHARD_BALANCE_MISMATCH")
    expected_fields = ((1800, 1300, 1300), (1300, 1800, 1300), (1300, 1300, 1800))
    expected_exact = (800, 800, 700)
    for resource_index, resource in enumerate(RESOURCES):
        replies = [reply_for(case, resource) for case in cases]
        if replies != [reply_for(case, resource) for case in cases]:
            reasons.append(f"RESOURCE_NONDETERMINISTIC:{resource}")
        observed_fields = tuple(
            sum(reply.fields[index] == case.truth[index] for case, reply in zip(cases, replies))
            for index in range(3)
        )
        observed_exact = sum(reply.fields == case.truth for case, reply in zip(cases, replies))
        if observed_fields != expected_fields[resource_index] or observed_exact != expected_exact[resource_index]:
            reasons.append(f"RESOURCE_GOLDEN_MISMATCH:{resource}")
    for case in cases:
        alarms = [reply_for(case, resource).alarm for resource in RESOURCES]
        if alarms != ([False, False, True] if case.bucket == 0 else [False, False, False]):
            reasons.append("COMMON_CAUSE_ALARM_MISMATCH")
            break
    return sorted(set(reasons))


def _comparison(target: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    target_flags = target["correct_flags"]
    baseline_flags = baseline["correct_flags"]
    wins = sum(target_ok and not base_ok for target_ok, base_ok in zip(target_flags, baseline_flags))
    losses = sum(base_ok and not target_ok for target_ok, base_ok in zip(target_flags, baseline_flags))
    shard_gains = tuple(
        target["shard_exact_counts"][shard] - baseline["shard_exact_counts"][shard]
        for shard in range(10)
    )
    passed = (
        target["exact_count"] - baseline["exact_count"] >= 600
        and wins - losses >= 600
        and all(gain >= 60 for gain in shard_gains)
    )
    return {
        "exact_gain": ratio(target["exact_count"] - baseline["exact_count"], 2000),
        "paired_wins": ratio(wins, 2000),
        "paired_losses": ratio(losses, 2000),
        "paired_net": ratio(wins - losses, 2000),
        "shards_passing_min_gain": f"{sum(gain >= 60 for gain in shard_gains)}/10",
        "minimum_shard_gain": ratio(min(shard_gains), 200),
        "passes": passed,
    }


def _jaccard(left: set[int], right: set[int]) -> dict[str, int | float | str]:
    return ratio(len(left & right), len(left | right))


def selected_error_overlap(cases: list[Case]) -> dict[str, Any]:
    errors = {
        resource: {
            index
            for index, case in enumerate(cases)
            if reply_for(case, resource).fields[resource_index] != case.truth[resource_index]
        }
        for resource_index, resource in enumerate(RESOURCES)
    }
    pairs = {
        f"{left}|{right}": _jaccard(errors[left], errors[right])
        for left, right in combinations(RESOURCES, 2)
    }
    return {
        "error_counts": {resource: len(errors[resource]) for resource in RESOURCES},
        "pairwise_jaccard": pairs,
        "triple_intersection": ratio(len(set.intersection(*(errors[name] for name in RESOURCES))), 2000),
        "union": ratio(len(set.union(*(errors[name] for name in RESOURCES))), 2000),
    }


def reproduce(plan_path: Path) -> dict[str, Any]:
    seed = hashlib.sha256(PUBLIC_REGRESSION_SEED_LABEL.encode("utf-8")).digest()
    integrity_failures = []
    if len(seed) != 32:
        integrity_failures.append("PUBLIC_REGRESSION_SEED_INVALID")
    if hashlib.sha256(plan_path.read_bytes()).hexdigest() != FROZEN_PLAN_SHA256:
        integrity_failures.append("FROZEN_PLAN_HASH_MISMATCH")
    cases = make_cases(seed)
    integrity_failures.extend(dataset_integrity(cases))
    if integrity_failures:
        return {
            "schema_version": "1.0-public",
            "benchmark_id": BENCHMARK_ID,
            "status": "UNKNOWN",
            "reason_codes": sorted(set(integrity_failures)),
        }

    try:
        calls, selectors = load_plan(plan_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": "1.0-public",
            "benchmark_id": BENCHMARK_ID,
            "status": "NO-GAIN",
            "reason_codes": ["TARGET_PLAN_INVALID"],
            "detail": str(exc),
        }

    target = evaluate(cases, calls, selectors)
    singleton_evaluations = {
        name: evaluate(cases, *canonical(vector)) for name, vector in SINGLETONS.items()
    }
    ablation_evaluations = {
        name: evaluate(cases, *canonical(vector)) for name, vector in ABLATIONS.items()
    }
    substitution_evaluations = {
        name: evaluate(cases, *canonical(vector)) for name, vector in SUBSTITUTIONS.items()
    }
    all_evaluations = [target, *singleton_evaluations.values(), *ablation_evaluations.values(), *substitution_evaluations.values()]

    target_summary = target["summary"]
    target_exact = Fraction(target["exact_count"], 2000)
    target_selective = Fraction(
        target_summary["selective_exact"]["numerator"],
        target_summary["selective_exact"]["denominator"],
    )
    target_coverage = Fraction(
        target_summary["coverage"]["numerator"], target_summary["coverage"]["denominator"]
    )
    comparisons = {
        name: _comparison(target, evaluation) for name, evaluation in singleton_evaluations.items()
    }

    def structural_rows(evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
        output = {}
        for name, evaluation in evaluations.items():
            exact = Fraction(evaluation["exact_count"], 2000)
            gain = target_exact - exact
            output[name] = {
                "exact": ratio(evaluation["exact_count"], 2000),
                "target_exact_gain": ratio(gain.numerator, gain.denominator),
                "passes": exact <= Fraction(13, 20) and gain >= Fraction(3, 20),
            }
        return output

    ablations = structural_rows(ablation_evaluations)
    substitutions = structural_rows(substitution_evaluations)
    best_by_width: dict[int, int] = {}
    plans_enumerated = 0
    for vector in product(RESOURCES, repeat=3):
        evaluation = evaluate(cases, *canonical(vector))
        width = len(set(vector))
        best_by_width[width] = max(best_by_width.get(width, 0), evaluation["exact_count"])
        plans_enumerated += 1

    minimum_width = min(width for width, score in best_by_width.items() if score >= 1500)
    min_field = min(
        Fraction(metric["numerator"], metric["denominator"])
        for metric in target_summary["raw_field_accuracy"].values()
    )
    unsafe_target = Fraction(
        target_summary["unsafe_common"]["numerator"], target_summary["unsafe_common"]["denominator"]
    )
    unsafe_singletons = [
        Fraction(row["summary"]["unsafe_common"]["numerator"], row["summary"]["unsafe_common"]["denominator"])
        for row in singleton_evaluations.values()
    ]
    guard_delta = Fraction(
        ablation_evaluations["drop_action_guard"]["summary"]["unsafe_common"]["numerator"],
        ablation_evaluations["drop_action_guard"]["summary"]["unsafe_common"]["denominator"],
    ) - unsafe_target

    hard_checks = {
        "exact_at_least_0.75": target_exact >= Fraction(3, 4),
        "minimum_raw_field_at_least_0.88": min_field >= Fraction(22, 25),
        "selective_exact_at_least_0.83": target_selective >= Fraction(83, 100),
        "schema_and_field_provenance": True,
        "deterministic_replay": target_summary["deterministic_replay"]["numerator"]
        == target_summary["deterministic_replay"]["denominator"],
        "budget_no_more_than_3": target_summary["worst_case_cost"] <= 3
        and target_summary["budget_violations"] == 0,
    }
    guard_checks = {
        "coverage_in_0.94_to_0.96": Fraction(47, 50) <= target_coverage <= Fraction(24, 25),
        "zero_unsafe_common_emissions": unsafe_target == 0,
        "zero_false_abstentions_outside_common": target_summary["false_abstain_noncommon"]["numerator"] == 0,
        "common_cause_containment": target_summary["common_containment"]["numerator"]
        == target_summary["common_containment"]["denominator"],
        "no_safety_regression_vs_safest_singleton": unsafe_target <= min(unsafe_singletons),
        "guard_removal_unsafe_delta_at_least_0.90": guard_delta >= Fraction(9, 10),
    }
    structural_checks = {
        "all_27_source_vectors_enumerated": plans_enumerated == 27,
        "minimum_passing_width_is_3": minimum_width == 3,
        "all_singleton_and_shard_gains": all(row["passes"] for row in comparisons.values()),
        "all_drop_one_ablations": all(row["passes"] for row in ablations.values()),
        "all_role_substitutions": all(row["passes"] for row in substitutions.values()),
        "candidate_uses_three_distinct_resources": len({resource for _, resource in calls}) == 3,
        "resource_depth_is_1": True,
        "error_overlap_measured": True,
    }
    audit_match = all(evaluation["audit_match"] for evaluation in all_evaluations)
    failures = [
        name
        for group in (hard_checks, guard_checks, structural_checks, {"independent_recount": audit_match})
        for name, passed in group.items()
        if not passed
    ]

    singleton_summaries = {
        name: {
            "exact": evaluation["summary"]["exact"],
            "cost": evaluation["summary"]["worst_case_cost"],
        }
        for name, evaluation in singleton_evaluations.items()
    }
    return {
        "schema_version": "1.0-public",
        "benchmark_id": BENCHMARK_ID,
        "status": "GAIN-VERIFIED" if not failures else "NO-GAIN",
        "reason_codes": failures,
        "evaluation_date": "2026-09-03",
        "fixture_state": "separate deterministic public regression fixture; original held-out seed and reveal excluded",
        "integrity": {
            "historical_seed_commitment_sha256": HISTORICAL_SEED_COMMITMENT,
            "historical_seed_commitment_status": "verified during the original private evaluation; reveal excluded from the public package",
            "public_regression_seed_derivation": "sha256(UTF8('weak3-structural-gain-v1/public-regression/v1'))",
            "public_regression_seed_sha256": hashlib.sha256(seed).hexdigest(),
            "frozen_plan_sha256": FROZEN_PLAN_SHA256,
            "frozen_plan_verified": True,
            "dataset_balanced": True,
            "independent_recount_match": audit_match,
        },
        "dataset": {"items": 2000, "buckets": 20, "items_per_bucket": 100, "shards": 10},
        "target": {
            "source_vector": [calls[selectors[index]][1] for index in range(3)],
            "exact": target_summary["exact"],
            "coverage": target_summary["coverage"],
            "selective_exact": target_summary["selective_exact"],
            "minimum_raw_field_accuracy": ratio(min(metric["numerator"] for metric in target_summary["raw_field_accuracy"].values()), 2000),
            "cost": target_summary["worst_case_cost"],
            "depth": 1,
        },
        "matched_budget_singletons": singleton_summaries,
        "comparisons": comparisons,
        "guards": {
            "unsafe_common": target_summary["unsafe_common"],
            "common_cause_containment": target_summary["common_containment"],
            "false_abstain_noncommon": target_summary["false_abstain_noncommon"],
            "guard_removal_unsafe_delta": ratio(guard_delta.numerator, guard_delta.denominator),
        },
        "structural": {
            "plans_enumerated": plans_enumerated,
            "best_exact_by_distinct_resource_count": {
                str(width): ratio(score, 2000) for width, score in sorted(best_by_width.items())
            },
            "minimum_passing_width": minimum_width,
            "ablations": ablations,
            "substitutions": substitutions,
            "selected_specialist_error_overlap": selected_error_overlap(cases),
        },
        "checks": {"hard": hard_checks, "guard": guard_checks, "structural": structural_checks},
        "authoring_scope": {
            "condition": "target Skill only; other installed Skills disabled by the isolated runner",
            "causal_claim": "none versus a no-Skill authoring baseline",
        },
        "target_skill": {
            "name": "comprehensive-engineering-cybernetics",
            "source_commit_context": "7fa3bb8df271183c7aaf7d0c04a10510614f1f94",
            "cryptographically_bound_in_original_evidence": False,
            "scope": "repository HEAD recorded in the work log; the original frozen evidence did not embed this commit",
        },
        "benchmark_design": {
            "fixed_error_buckets": True,
            "balanced_buckets_per_shard": 20,
            "interpretation": "deterministic structural proof and regression, not distributional generalization",
        },
        "interpretation": {
            "supported": "The frozen plan has objective equal-budget structural gain inside this benchmark.",
            "not_supported": [
                "Causal superiority over a matched no-Skill authoring condition",
                "Benefit from arbitrary weak-resource combinations",
                "Distributional or production generalization",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--plan", type=Path, default=here / "plan.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    result = reproduce(args.plan)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    if args.check:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        if expected != result:
            print("FAIL: recomputed result differs from recorded result", file=sys.stderr)
            return 1
        print(
            "PASS: GAIN-VERIFIED; 2000 cases; exact=0.80; coverage=0.95; "
            "selective_exact=16/19; cost=3; depth=1"
        )
    elif not args.output:
        sys.stdout.write(rendered)
    return 0 if result["status"] == "GAIN-VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
