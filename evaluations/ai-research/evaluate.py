#!/usr/bin/env python3
"""Audit the public CEC-MiniResearch-1 record without rerunning hidden data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


SUBMISSION_SHA256 = "51ca953d0eee5390b35657a9538a67853fe5bc797909e3d356c302208ceece0e"
PUBLISHED_SNAPSHOT_COMMIT = "3278710dc8a141a5ecb9a7651c86ea2b9da631e6"
EVALUATED_SKILL_SHA256 = "14b6fd6a1e831baf92853bb6f9e9c1fa1b473bc2f1343548522daf9350100fb0"
EVALUATED_AI_REFERENCE_SHA256 = "138c0a49eedfa9159e669e4067360ccaa544eee32a20c77b596ec6012b942e8c"

TERM_COST = {
    "raw": 1,
    "square": 2,
    "product": 2,
    "hinge": 2,
    "hinge_product": 3,
    "absdiff": 2,
}

JUDGE_WEIGHTS = {
    "mechanistic_insight_and_distinctness": 30,
    "fair_rival_and_falsifiability": 25,
    "heldout_and_ablation_logic": 20,
    "economy_and_claim_to_model_coherence": 15,
    "epistemic_calibration": 10,
}


class AuditError(ValueError):
    """Raised when a public record fails a deterministic audit."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_nonfinite(token: str) -> None:
    raise AuditError(f"non-finite JSON number: {token}")


def load_json_strict(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    require(not raw.startswith(b"\xef\xbb\xbf"), f"{path.name}: UTF-8 BOM is forbidden")
    text = raw.decode("utf-8")
    value = json.loads(
        text,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )
    require(isinstance(value, dict), f"{path.name}: root must be an object")
    validate_json_tree(value, path.name)
    return value


def validate_json_tree(value: Any, label: str) -> None:
    if isinstance(value, float):
        require(math.isfinite(value), f"{label}: non-finite value")
    elif isinstance(value, dict):
        require(all(isinstance(key, str) for key in value), f"{label}: non-string key")
        for key, child in value.items():
            validate_json_tree(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_json_tree(child, f"{label}[{index}]")
    else:
        require(
            value is None or isinstance(value, (str, int, bool)),
            f"{label}: unsupported JSON value type",
        )


def exact(label: str, actual: Any, expected: Any) -> None:
    require(actual == expected, f"{label}: expected {expected!r}, got {actual!r}")


def exact_keys(label: str, actual: dict[str, Any], expected: set[str]) -> None:
    require(isinstance(actual, dict), f"{label}: expected object")
    keys = set(actual)
    require(keys == expected, f"{label}: key mismatch; expected {sorted(expected)}, got {sorted(keys)}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_submission(path: Path) -> dict[str, Any]:
    require(path.stat().st_size <= 65536, "submission exceeds 64 KiB")
    digest = sha256(path)
    exact("submission SHA-256", digest, SUBMISSION_SHA256)
    submission = load_json_strict(path)

    exact("submission schema", submission.get("schema_version"), "1.0")
    ideas = submission.get("ideas")
    require(isinstance(ideas, list) and len(ideas) == 3, "submission must contain exactly 3 ideas")
    idea_ids: list[str] = []
    required_idea_fields = (
        "id",
        "mechanism",
        "directional_prediction",
        "cheapest_test",
        "falsifying_observation",
    )
    for index, idea in enumerate(ideas):
        require(isinstance(idea, dict), f"idea {index}: expected object")
        for field in required_idea_fields:
            require(isinstance(idea.get(field), str) and idea[field].strip(), f"idea {index}: missing {field}")
        idea_ids.append(idea["id"])
    require(len(set(idea_ids)) == 3, "idea IDs must be distinct")
    require(submission.get("selected_idea_id") in idea_ids, "selected idea does not exist")

    hypothesis = submission.get("hypothesis")
    require(isinstance(hypothesis, dict), "hypothesis must be an object")
    variables = hypothesis.get("mechanism_variables")
    require(isinstance(variables, list) and variables, "mechanism variables are required")
    require(all(isinstance(value, str) for value in variables), "mechanism variables must be strings")
    exact("hypothesis expected sign", hypothesis.get("expected_sign"), "positive")

    model = submission.get("primary_model")
    require(isinstance(model, dict), "primary model must be an object")
    terms = model.get("terms")
    require(isinstance(terms, list) and len(terms) <= 6, "primary model term budget violated")
    term_ids: list[str] = []
    total_cost = 0
    mechanism_terms: list[dict[str, Any]] = []
    raw_support_variables: set[str] = set()
    for index, term in enumerate(terms):
        require(isinstance(term, dict), f"term {index}: expected object")
        term_id = term.get("id")
        op = term.get("op")
        columns = term.get("columns")
        require(isinstance(term_id, str) and term_id, f"term {index}: missing ID")
        require(op in TERM_COST, f"term {index}: unknown operation")
        require(isinstance(columns, list) and columns, f"term {index}: columns are required")
        require(all(isinstance(column, str) for column in columns), f"term {index}: invalid column")
        term_ids.append(term_id)
        total_cost += TERM_COST[op]
        if term.get("role") == "mechanism":
            mechanism_terms.append(term)
        if term.get("role") == "support" and op == "raw" and len(columns) == 1:
            raw_support_variables.add(columns[0])

    require(len(set(term_ids)) == len(term_ids), "term IDs must be distinct")
    exact("public example term count", len(terms), 5)
    exact("public example weighted term cost", total_cost, 7)
    require(total_cost <= 9, "weighted term cost budget violated")
    require(mechanism_terms, "at least one mechanism term is required")
    covered = {column for term in mechanism_terms for column in term["columns"]}
    require(set(variables) <= covered, "mechanism term does not cover all mechanism variables")
    require(
        set(variables) <= raw_support_variables,
        "incremental high-order claim lacks matched raw main effects",
    )
    require(
        any(term["op"] == "hinge_product" and set(term["columns"]) == set(variables) for term in mechanism_terms),
        "expected nested hinge-product mechanism is absent",
    )

    claims = submission.get("claims")
    require(isinstance(claims, list) and claims, "claims are required")
    known_terms = set(term_ids)
    for index, claim in enumerate(claims):
        require(isinstance(claim, dict), f"claim {index}: expected object")
        refs = claim.get("model_term_refs")
        require(isinstance(refs, list) and refs, f"claim {index}: model references required")
        require(set(refs) <= known_terms, f"claim {index}: unknown model-term reference")

    exact(
        "public example metrics",
        submission.get("public_results"),
        {
            "primary_rmse": 0.11910300154563654,
            "rival_rmse": 0.39524925783617426,
            "relative_rmse_lift_vs_additive_rival": 0.6986635668902301,
        },
    )
    ceiling = submission.get("evidence_ceiling")
    require(isinstance(ceiling, dict), "evidence ceiling is required")
    exact("evidence ceiling", ceiling.get("level"), "predictive_association_under_observed_interventions")
    limitations = ceiling.get("limitations")
    require(isinstance(limitations, list) and len(limitations) >= 3, "at least 3 limitations are required")
    return submission


INITIAL_Q_METRICS = {
    "public": {
        "primary_rmse": 0.11910300154563654,
        "rival_rmse": 0.39524925783617426,
        "relative_rmse_lift_vs_additive_rival": 0.6986635668902301,
    },
    "factorial": {
        "rmse": 0.1238922934297558,
        "mae": 0.10014374158757812,
        "nrmse": 0.11101131021753105,
        "baseline_rmse": 1.12389468048537,
        "baseline_improvement": 0.8897652105833874,
        "rival_rmse": 0.7067299662142871,
        "additive_rival_lift": 0.8246964196333646,
    },
    "shadow": {
        "rmse": 0.13431351209737938,
        "mae": 0.1129212135134375,
        "nrmse": 0.15920193236379035,
        "baseline_rmse": 0.8466875567758293,
        "baseline_improvement": 0.8413659076214102,
    },
    "boundary": {
        "rmse": 0.12427991028904332,
        "mae": 0.0995371202284375,
        "nrmse": 0.36873750146697953,
        "baseline_rmse": 0.40149867506228554,
        "baseline_improvement": 0.6904599740714874,
    },
    "declared_direction_coefficient": 0.6120728741494618,
}

INITIAL_R_METRICS = {
    "public": {
        "primary_rmse": 0.1332353844878441,
        "rival_rmse": 0.3952492578361741,
        "relative_rmse_lift_vs_additive_rival": 0.6629079451856466,
    },
    "factorial": {
        "rmse": 0.1386833227299649,
        "mae": 0.11559788811226562,
        "nrmse": 0.12426452796519559,
        "baseline_rmse": 1.12389468048537,
        "baseline_improvement": 0.8766046986982157,
        "rival_rmse": 0.706729966214287,
        "additive_rival_lift": 0.8037675924896117,
    },
    "shadow": {
        "rmse": 0.1571580405500086,
        "mae": 0.13401681981583333,
        "nrmse": 0.18627957344997798,
        "baseline_rmse": 0.8466875567758293,
        "baseline_improvement": 0.8143848468159098,
    },
    "boundary": {
        "rmse": 0.12601401830521772,
        "mae": 0.10054971832765626,
        "nrmse": 0.3738825861043184,
        "baseline_rmse": 0.40149867506228554,
        "baseline_improvement": 0.6861408863038743,
    },
    "declared_direction_coefficient": 0.6530620847909291,
}

REGRESSION_METRICS = {
    "public": {
        "primary_rmse": 0.11910300154563654,
        "rival_rmse": 0.39524925783617426,
        "relative_rmse_lift_vs_additive_rival": 0.6986635668902301,
    },
    "factorial": {
        "rmse": 0.11551703091817248,
        "mae": 0.09193590001421877,
        "nrmse": 0.10329295109679625,
        "baseline_rmse": 1.1256578568730933,
        "baseline_improvement": 0.8973782040316751,
        "rival_rmse": 0.702730994248741,
        "additive_rival_lift": 0.8356169973096652,
    },
    "shadow": {
        "rmse": 0.12274207191712698,
        "mae": 0.09827050082666666,
        "nrmse": 0.12891219125043282,
        "baseline_rmse": 0.952414633701912,
        "baseline_improvement": 0.871125382187751,
    },
    "boundary": {
        "rmse": 0.12055033947704347,
        "mae": 0.09775127909609374,
        "nrmse": 0.3597009580854465,
        "baseline_rmse": 0.40834973048599504,
        "baseline_improvement": 0.7047865335099617,
    },
    "declared_direction_coefficient": 0.6120728741494618,
}


def audit_machine_condition(
    label: str,
    condition: dict[str, Any],
    term_count: int,
    weighted_cost: int,
    tokens: dict[str, int],
    metrics: dict[str, Any] | None = None,
) -> None:
    exact(f"{label} machine gates", condition.get("machine_gates"), {"passed": 15, "total": 15})
    exact(f"{label} hypothesis verdict", condition.get("hypothesis_verdict"), "supported")
    exact(
        f"{label} complexity",
        condition.get("complexity"),
        {"term_count": term_count, "weighted_cost": weighted_cost},
    )
    exact(f"{label} tokens", condition.get("tokens"), tokens)
    if metrics is not None:
        exact(f"{label} metrics", condition.get("metrics"), metrics)


def weighted_total(scores: dict[str, int]) -> float:
    exact_keys("judge dimension scores", scores, set(JUDGE_WEIGHTS))
    for dimension, value in scores.items():
        require(isinstance(value, int) and 0 <= value <= 5, f"invalid score for {dimension}")
    return sum(scores[name] * weight / 5 for name, weight in JUDGE_WEIGHTS.items())


def audit_blind_summary(
    label: str,
    blind: dict[str, Any],
    expected_scores: dict[str, dict[str, float]],
    expected_preferences: dict[str, str],
    expected_winner: str,
) -> None:
    exact(f"{label} orders", blind.get("orders"), {"forward": ["Q", "R"], "reverse": ["R", "Q"]})
    scores = blind.get("valid_scores_by_candidate")
    exact(f"{label} valid candidate scores", scores, expected_scores)
    for candidate in ("Q", "R"):
        calculated_mean = (scores[candidate]["forward"] + scores[candidate]["reverse"]) / 2
        exact(f"{label} {candidate} mean", scores[candidate]["mean"], calculated_mean)
    exact(f"{label} preferences", blind.get("preferences"), expected_preferences)
    deltas = {
        candidate: abs(scores[candidate]["forward"] - scores[candidate]["reverse"])
        for candidate in ("Q", "R")
    }
    exact(f"{label} position deltas", blind.get("position_sensitivity_delta"), deltas)
    exact(f"{label} position-sensitive flag", blind.get("position_sensitive"), any(value > 8 for value in deltas.values()))

    preferences = list(expected_preferences.values())
    if preferences[0] == preferences[1] and preferences[0] in {"Q", "R"}:
        preferred = preferences[0]
        other = "R" if preferred == "Q" else "Q"
        margin = scores[preferred]["mean"] - scores[other]["mean"]
        calculated_winner = preferred if margin >= 5 else "tie"
    else:
        calculated_winner = "tie"
    exact(f"{label} frozen-rule winner", blind.get("winner"), calculated_winner)
    exact(f"{label} expected winner", calculated_winner, expected_winner)


def audit_result(result: dict[str, Any], submission_path: Path) -> None:
    exact_keys(
        "result root",
        result,
        {
            "schema_version",
            "benchmark_id",
            "evaluation_date",
            "fixture_state",
            "public_artifact",
            "initial_ab",
            "closed_loop_fix",
            "targeted_regression",
            "interpretation",
            "public_audit_scope",
        },
    )
    exact("result schema", result["schema_version"], "1.0-public")
    exact("benchmark ID", result["benchmark_id"], "CEC-MiniResearch-1")
    exact("evaluation date", result["evaluation_date"], "2026-09-03")

    public_artifact = result["public_artifact"]
    exact("result submission hash", public_artifact.get("submission_sha256"), sha256(submission_path))
    exact("result public term count", public_artifact.get("term_count"), 5)
    exact("result public weighted cost", public_artifact.get("weighted_cost"), 7)
    exact("result nested main effects", public_artifact.get("nested_main_effects_verified"), True)

    fix = result["closed_loop_fix"]
    exact_keys(
        "closed-loop fix",
        fix,
        {
            "trigger",
            "published_snapshot_commit",
            "snapshot_provenance",
            "evaluated_skill_sha256",
            "evaluated_ai_research_reference_sha256",
            "changes",
            "evidence_status",
        },
    )
    exact("published snapshot commit", fix.get("published_snapshot_commit"), PUBLISHED_SNAPSHOT_COMMIT)
    exact(
        "snapshot provenance",
        fix.get("snapshot_provenance"),
        "post-evaluation byte-identical public snapshot; not a contemporaneous runtime binding",
    )
    exact("evaluated Skill hash", fix.get("evaluated_skill_sha256"), EVALUATED_SKILL_SHA256)
    exact(
        "evaluated AI reference hash",
        fix.get("evaluated_ai_research_reference_sha256"),
        EVALUATED_AI_REFERENCE_SHA256,
    )
    changes = fix.get("changes")
    require(isinstance(changes, list) and len(changes) == 2, "exactly two closed-loop fixes must be recorded")

    initial = result["initial_ab"]
    q_initial = initial["Q_no_skill"]
    r_initial = initial["R_target_skill"]
    audit_machine_condition(
        "initial Q",
        q_initial,
        5,
        7,
        {"input": 307419, "cached_input": 285824, "output": 6993, "reasoning_output": 848},
        INITIAL_Q_METRICS,
    )
    audit_machine_condition(
        "initial R",
        r_initial,
        3,
        5,
        {"input": 561871, "cached_input": 515328, "output": 7806, "reasoning_output": 1054},
        INITIAL_R_METRICS,
    )
    require(
        q_initial["metrics"]["public"]["primary_rmse"] < r_initial["metrics"]["public"]["primary_rmse"]
        and q_initial["metrics"]["public"]["relative_rmse_lift_vs_additive_rival"]
        > r_initial["metrics"]["public"]["relative_rmse_lift_vs_additive_rival"]
        and q_initial["metrics"]["factorial"]["nrmse"] < r_initial["metrics"]["factorial"]["nrmse"]
        and q_initial["metrics"]["factorial"]["additive_rival_lift"]
        > r_initial["metrics"]["factorial"]["additive_rival_lift"]
        and q_initial["metrics"]["shadow"]["nrmse"] < r_initial["metrics"]["shadow"]["nrmse"]
        and q_initial["metrics"]["boundary"]["mae"] < r_initial["metrics"]["boundary"]["mae"],
        "initial Q was not better on every declared predictive comparison",
    )
    initial_resource = initial["resource_comparison"]
    exact("initial input-token difference", initial_resource.get("target_minus_baseline_input_tokens"), 561871 - 307419)
    exact(
        "initial input-token percentage",
        initial_resource.get("target_input_token_increase_percent"),
        round((561871 / 307419 - 1) * 100, 6),
    )
    exact("initial resource-savings verdict", initial_resource.get("end_to_end_resource_savings_supported"), False)
    audit_blind_summary(
        "initial blind judgment",
        initial["blind_judgment"],
        {
            "Q": {"forward": 100, "reverse": 100, "mean": 100},
            "R": {"forward": 66, "reverse": 74, "mean": 70},
        },
        {"forward": "Q", "reverse": "Q"},
        "Q",
    )
    exact("initial blind margin", initial["blind_judgment"].get("mean_margin"), 30)
    verdict = initial["comparative_verdict"]
    exact("initial Skill advantage verdict", verdict.get("skill_quality_advantage_supported"), False)
    require(len(initial.get("protocol_deviations", [])) >= 8, "initial protocol deviations are incomplete")

    regression = result["targeted_regression"]
    require("not independent validation" in regression.get("independence_status", ""), "regression independence boundary missing")
    audit_machine_condition(
        "regression Q",
        regression["Q_no_skill"],
        5,
        7,
        {"input": 353634, "cached_input": 329472, "output": 9259, "reasoning_output": 1079},
    )
    audit_machine_condition(
        "regression R",
        regression["R_revised_skill"],
        5,
        7,
        {"input": 552310, "cached_input": 510848, "output": 7800, "reasoning_output": 1056},
    )
    exact("regression shared metrics", regression.get("identical_machine_metrics"), REGRESSION_METRICS)
    exact(
        "regression public metrics versus sample",
        regression["identical_machine_metrics"]["public"],
        load_json_strict(submission_path)["public_results"],
    )
    regression_resource = regression["resource_comparison"]
    exact("regression input-token difference", regression_resource.get("R_minus_Q_input_tokens"), 552310 - 353634)
    exact(
        "regression input-token percentage",
        regression_resource.get("R_input_token_increase_percent"),
        round((552310 / 353634 - 1) * 100, 6),
    )
    exact("regression resource-savings verdict", regression_resource.get("end_to_end_resource_savings_supported"), False)

    blind = regression["blind_judgment"]
    discarded = blind["discarded_forward_attempt"]
    scores = discarded["dimension_scores"]
    recomputed = {
        "first_Q": weighted_total(scores["first_Q"]),
        "second_R": weighted_total(scores["second_R"]),
    }
    exact("discarded judge recomputation", discarded.get("recomputed_totals"), recomputed)
    require(
        discarded["self_reported_totals"]["first_Q"] != recomputed["first_Q"]
        and discarded["self_reported_totals"]["second_R"] == recomputed["second_R"],
        "discarded judge mismatch is not reproduced",
    )
    exact("discarded judge acceptance", discarded.get("accepted"), False)
    audit_blind_summary(
        "regression blind judgment",
        blind,
        {
            "Q": {"forward": 96, "reverse": 95, "mean": 95.5},
            "R": {"forward": 96, "reverse": 100, "mean": 98},
        },
        {"forward": "tie", "reverse": "R"},
        "tie",
    )
    regression_verdict = regression["verdict"]
    exact("regression machine metric difference", regression_verdict.get("machine_metric_difference"), 0)
    exact("regression comparative winner", regression_verdict.get("comparative_quality_winner"), "tie")
    exact("regression Skill advantage verdict", regression_verdict.get("skill_quality_advantage_supported"), False)
    exact("regression resource savings verdict", regression_verdict.get("end_to_end_resource_savings_supported"), False)

    interpretation = result["interpretation"]
    require(isinstance(interpretation.get("not_supported"), list), "not-supported boundaries are required")
    not_supported = " ".join(interpretation["not_supported"]).lower()
    for required_phrase in ("quality advantage", "resource savings", "causal", "independent"):
        require(required_phrase in not_supported, f"missing interpretation boundary: {required_phrase}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, required=True, help="public result JSON to audit")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    result_path = args.check if args.check.is_absolute() else Path.cwd() / args.check
    submission_path = here / "submission.json"
    try:
        audit_submission(submission_path)
        result = load_json_strict(result_path)
        audit_result(result, submission_path)
    except (AuditError, OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: PUBLIC-AUDIT; initial Q no-Skill won 100-70; "
        "targeted regression passed 15/15 for both and remained a blind-judgment tie; "
        "no Skill quality or end-to-end resource-saving advantage is claimed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
