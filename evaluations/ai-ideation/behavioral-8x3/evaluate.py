#!/usr/bin/env python3
"""Deterministically audit and aggregate CEC-AIIdea-8x3-Dev-1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
TASKS = [f"IDEA-{index:02d}" for index in range(1, 9)]
ARMS = ["no_skill", "legacy", "current"]
LABELS = ["X", "Y", "Z"]
ORDERS = {
    "forward": ["X", "Y", "Z"],
    "reverse": ["Z", "Y", "X"],
}
PAIR_ORDERS = {
    "forward": [["X", "Y"], ["X", "Z"], ["Y", "Z"]],
    "reverse": [["Z", "Y"], ["Z", "X"], ["Y", "X"]],
}
ARM_PAIRS = [["current", "no_skill"], ["current", "legacy"], ["no_skill", "legacy"]]
WEIGHTS = {"D1": 12, "D2": 18, "D3": 14, "D4": 18, "D5": 14, "D6": 12, "D7": 8, "D8": 4}
KEY_DIMENSIONS = ["D1", "D2", "D4", "D5", "D6"]
CAPS = {"IDEA-01": 550, "IDEA-02": 550, **{f"IDEA-{index:02d}": 600 for index in range(3, 9)}}
ATTESTATION_KEYS = {
    "used_tools",
    "read_files",
    "used_web",
    "used_other_skills",
    "used_subagents",
    "used_cross_run_memory",
}
JUDGE_TOP_LEVEL_KEYS = {
    "schema_version",
    "task_id",
    "presentation_order",
    "candidates",
    "pairwise",
    "ranking",
    "position_or_length_concern",
    "most_decisive_evidence",
}
JUDGE_CANDIDATE_KEYS = {
    "dimensions",
    "weighted_total",
    "objective_invalid",
    "invalid_reason",
}
JUDGE_PAIR_KEYS = {"left", "right", "winner", "reason"}
FORBIDDEN_TEXT = [
    "no_skill",
    "legacy",
    "current",
    "skill",
    "comprehensive-engineering-cybernetics",
    "工程控制论",
    "3278710dc8a141a5ecb9a7651c86ea2b9da631e6",
    "43501b979d47dc83ebe59e35154cbb27f26141d5",
    "http://",
    "https://",
    ".planning",
    "c:\\",
]


class DuplicateKeyError(ValueError):
    pass


def _unique_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite number: {value}")
    return parsed


def strict_json_bytes(data: bytes) -> Any:
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    return json.loads(
        data.decode("utf-8", "strict"),
        object_pairs_hook=_unique_pairs,
        parse_float=_finite_float,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")),
    )


def strict_json_file(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def clean_number(value: float) -> int | float:
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def med(values: list[float]) -> int | float:
    return clean_number(statistics.median(values))


def avg(values: list[float]) -> int | float:
    return clean_number(statistics.fmean(values))


def weighted_total(dimensions: dict[str, Any]) -> float:
    return sum(float(dimensions[key]["score"]) / 4.0 * weight for key, weight in WEIGHTS.items())


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    xbar = statistics.fmean(xs)
    ybar = statistics.fmean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    xnorm = math.sqrt(sum((x - xbar) ** 2 for x in xs))
    ynorm = math.sqrt(sum((y - ybar) ** 2 for y in ys))
    return 0.0 if xnorm == 0 or ynorm == 0 else numerator / (xnorm * ynorm)


def normalized_winner(
    left: str,
    right: str,
    reported: str,
    totals: dict[str, float],
    invalid: dict[str, bool],
) -> str:
    if invalid[left] and not invalid[right]:
        return right
    if invalid[right] and not invalid[left]:
        return left
    if invalid[left] and invalid[right]:
        return "tie"
    delta = totals[left] - totals[right]
    if reported == left and delta >= 5:
        return left
    if reported == right and delta <= -5:
        return right
    return "tie"


def consolidate_pair(
    left: str,
    right: str,
    forward_winner: str,
    reverse_winner: str,
    forward_scores: dict[str, float],
    reverse_scores: dict[str, float],
) -> dict[str, Any]:
    drift = max(
        abs(forward_scores[left] - reverse_scores[left]),
        abs(forward_scores[right] - reverse_scores[right]),
    )
    winners = [winner for winner in [forward_winner, reverse_winner] if winner != "tie"]
    favored: str | None = None
    if forward_winner == reverse_winner and forward_winner != "tie":
        favored = forward_winner
        if drift <= 8:
            status = "strict_win" if favored == left else "strict_loss"
        else:
            status = "low_confidence_lean" if favored == left else "low_confidence_against"
    elif len(winners) == 1:
        favored = winners[0]
        status = "low_confidence_lean" if favored == left else "low_confidence_against"
    else:
        status = "tie_low_confidence"
    return {
        "left": left,
        "right": right,
        "forward": forward_winner,
        "reverse": reverse_winner,
        "max_candidate_score_drift": clean_number(drift),
        "status_from_left": status,
        "favored_arm": favored,
        "order_consistent": forward_winner == reverse_winner,
    }


def candidate_precheck(entry: dict[str, Any], task: str) -> tuple[dict[str, Any], str | None]:
    raw = entry["raw"]
    require(isinstance(raw, str), f"{task}: candidate raw must be text")
    raw_bytes = raw.encode("utf-8")
    require(sha256(raw_bytes) == entry["raw_sha256"], f"{task}: candidate raw hash mismatch")
    parsed: dict[str, Any] | None = None
    parse_error = ""
    try:
        value = strict_json_bytes(raw_bytes)
        if not isinstance(value, dict):
            raise ValueError("top level is not an object")
        parsed = value
    except Exception as exc:  # expected for the preserved IDEA-06 legacy failure
        parse_error = f"{type(exc).__name__}: {exc}"

    strict_valid = parsed is not None
    answer = parsed.get("answer") if parsed else None
    attestation = parsed.get("isolation_attestation") if parsed else None
    attestation_valid = (
        isinstance(attestation, dict)
        and set(attestation) == ATTESTATION_KEYS
        and all(attestation[key] is False for key in ATTESTATION_KEYS)
    )
    envelope_shape = parsed is not None and set(parsed) == {"answer", "isolation_attestation"}
    answer_codepoints = len(answer) if isinstance(answer, str) else None
    leakage_hits = []
    if isinstance(answer, str):
        lowered = answer.lower()
        leakage_hits = [token for token in FORBIDDEN_TEXT if token.lower() in lowered]
    envelope_valid = bool(
        envelope_shape
        and attestation_valid
        and isinstance(answer, str)
        and answer != ""
        and answer_codepoints is not None
        and answer_codepoints <= CAPS[task]
        and not leakage_hits
    )
    published = entry["precheck"]
    require(published["strict_json_valid"] == strict_valid, f"{task}: published strict JSON status mismatch")
    require(published["envelope_valid"] == envelope_valid, f"{task}: published envelope status mismatch")
    require(published["attestation_valid"] == attestation_valid, f"{task}: published attestation status mismatch")
    require(published["answer_codepoints"] == answer_codepoints, f"{task}: published length mismatch")
    require(published["answer_cap"] == CAPS[task], f"{task}: published cap mismatch")
    require(published["leakage_hits"] == leakage_hits, f"{task}: published leakage audit mismatch")

    run = entry["run"]
    require(run["model"] == "gpt-5.6-sol" and run["reasoning_effort"] == "high", f"{task}: candidate model mismatch")
    require(run["fresh_context"] is True and run["isolation_level"] == "prompt_trace_only", f"{task}: candidate isolation mismatch")
    require(run["retry_of"] is None, f"{task}: quality retry detected")
    expected_status = "completed" if strict_valid else "malformed"
    require(run["status"] == expected_status, f"{task}: candidate run status mismatch")
    require(run["usage"] == {"input_tokens": None, "output_tokens": None, "total_tokens": None, "available": False}, f"{task}: unsupported usage claim")
    return {
        "strict_json_valid": strict_valid,
        "envelope_valid": envelope_valid,
        "attestation_valid": attestation_valid,
        "answer_codepoints": answer_codepoints,
        "answer_cap": CAPS[task],
        "leakage_hits": leakage_hits,
        "parse_error": parse_error,
    }, answer if isinstance(answer, str) else None


def evaluate() -> dict[str, Any]:
    prerun = strict_json_file(HERE / "commitments/prerun.json")
    mapping_doc = strict_json_file(HERE / "reveal/anonymization.json")
    candidates_doc = strict_json_file(HERE / "artifacts/candidates.json")
    judgments_doc = strict_json_file(HERE / "artifacts/judgments.json")

    require(
        isinstance(mapping_doc, dict)
        and set(mapping_doc) == {"schema_version", "created_before_generation", "task_mappings", "judge_orders"},
        "mapping document shape mismatch",
    )
    require(mapping_doc["schema_version"] == "1.0" and mapping_doc["judge_orders"] == ORDERS, "mapping metadata mismatch")
    require(set(mapping_doc["task_mappings"]) == set(TASKS), "mapping task set mismatch")
    require(
        isinstance(candidates_doc, dict)
        and set(candidates_doc)
        == {"schema_version", "benchmark_id", "artifact_role", "source_freeze_sha256", "generation", "summary", "candidates"},
        "candidate artifact shape mismatch",
    )
    require(candidates_doc["schema_version"] == "1.0", "candidate artifact schema mismatch")
    require(is_sha256(candidates_doc["source_freeze_sha256"]), "candidate source-freeze hash shape mismatch")
    require(set(candidates_doc["candidates"]) == set(TASKS), "candidate task set mismatch")
    require(all(set(candidates_doc["candidates"][task]) == set(ARMS) for task in TASKS), "candidate arm set mismatch")
    require(
        isinstance(judgments_doc, dict)
        and set(judgments_doc)
        == {"schema_version", "benchmark_id", "artifact_role", "source_freeze_sha256", "judging", "summary", "judges"},
        "judgment artifact shape mismatch",
    )
    require(judgments_doc["schema_version"] == "1.0", "judgment artifact schema mismatch")
    require(is_sha256(judgments_doc["source_freeze_sha256"]), "judgment source-freeze hash shape mismatch")
    require(set(judgments_doc["judges"]) == set(TASKS), "judgment task set mismatch")
    require(all(set(judgments_doc["judges"][task]) == {"forward", "reverse"} for task in TASKS), "judgment order set mismatch")

    verified_files: dict[str, str] = {}
    for relative, expected in prerun["public_file_sha256"].items():
        actual = sha256((HERE / relative).read_bytes())
        require(actual == expected, f"preregistered public file changed: {relative}")
        verified_files[relative] = actual
    sealed_paths = {
        "TASKS.md": HERE / "TASKS.md",
        "EVALUATOR_KEYS.md": HERE / "EVALUATOR_KEYS.md",
        "anonymization.json": HERE / "reveal/anonymization.json",
    }
    for name, path in sealed_paths.items():
        actual = sha256(path.read_bytes())
        require(actual == prerun["sealed_commitments"][name], f"sealed reveal hash mismatch: {name}")
        verified_files[name] = actual
    current_paths = {
        "current/SKILL.md": REPO / "SKILL.md",
        "current/references/ai-ideation.md": REPO / "references/ai-ideation.md",
    }
    expected_current = {
        "current/SKILL.md": prerun["target_versions"]["current"]["skill_sha256"],
        "current/references/ai-ideation.md": prerun["target_versions"]["current"]["reference_sha256"],
    }
    for name, path in current_paths.items():
        actual = sha256(path.read_bytes())
        require(actual == expected_current[name], f"measured current bundle changed: {name}")
        verified_files[name] = actual

    require(candidates_doc["benchmark_id"] == prerun["evaluation_id"], "candidate benchmark identity mismatch")
    require(judgments_doc["benchmark_id"] == prerun["evaluation_id"], "judge benchmark identity mismatch")
    require(mapping_doc["created_before_generation"] is True, "mapping was not frozen before generation")
    mapping = mapping_doc["task_mappings"]

    prechecks: dict[str, dict[str, Any]] = {}
    answers: dict[str, dict[str, str | None]] = {}
    candidate_hashes: dict[str, dict[str, str]] = {}
    for task in TASKS:
        require(set(mapping[task]) == set(LABELS) and set(mapping[task].values()) == set(ARMS), f"{task}: mapping is not a permutation")
        prechecks[task] = {}
        answers[task] = {}
        candidate_hashes[task] = {}
        for arm in ARMS:
            entry = candidates_doc["candidates"][task][arm]
            checked, answer = candidate_precheck(entry, task)
            prechecks[task][arm] = checked
            answers[task][arm] = answer
            candidate_hashes[task][arm] = entry["raw_sha256"]
            bundle = entry["run"]["instruction_bundle"]
            if arm == "no_skill":
                require(bundle == {"kind": "none"}, f"{task}: no-skill bundle mismatch")
            else:
                target = prerun["target_versions"][arm]
                require(bundle["kind"] == arm and bundle["commit"] == target["commit"], f"{task}: bundle identity mismatch")
                require(bundle["skill_sha256"] == target["skill_sha256"] and bundle["reference_sha256"] == target["reference_sha256"], f"{task}: bundle hash mismatch")

    valid_count = sum(prechecks[task][arm]["envelope_valid"] for task in TASKS for arm in ARMS)
    require(valid_count == 22, "candidate valid count changed")
    require(candidates_doc["summary"]["valid"] == valid_count, "candidate summary mismatch")
    require(candidates_doc["summary"]["total"] == 24 and candidates_doc["summary"]["precheck_invalid"] == 2, "candidate accounting changed")
    require(
        candidates_doc["summary"]["invalid_candidates"]
        == [
            {"task_id": "IDEA-06", "arm_id": "legacy", "reason": "malformed JSON envelope"},
            {"task_id": "IDEA-07", "arm_id": "legacy", "reason": "answer length 780 exceeds 600-code-point cap"},
        ],
        "candidate invalid identities changed",
    )

    # Judge totals are recomputed from dimension scores. The raw reported totals remain audit-only.
    scores: dict[str, dict[str, dict[str, float]]] = {task: {} for task in TASKS}
    dimensions: dict[str, dict[str, dict[str, dict[str, float]]]] = {task: {} for task in TASKS}
    semantic_invalid: dict[str, dict[str, dict[str, bool]]] = {task: {} for task in TASKS}
    semantic_invalid_reasons: dict[str, dict[str, dict[str, str]]] = {task: {} for task in TASKS}
    normalized_pairs: dict[str, dict[str, dict[tuple[str, str], str]]] = {task: {} for task in TASKS}
    judgment_hashes: dict[str, dict[str, str]] = {task: {} for task in TASKS}
    mismatch_cells: list[dict[str, Any]] = []
    pairwise_downgrades: list[dict[str, Any]] = []
    quote_deviations: list[dict[str, Any]] = []
    semantic_invalid_cells: list[dict[str, str]] = []
    exact_math_judges = 0
    exact_pairwise_judges = 0
    precheck_exclusions_correct = 0

    for task in TASKS:
        inverse = {arm: label for label, arm in mapping[task].items()}
        for order in ["forward", "reverse"]:
            entry = judgments_doc["judges"][task][order]
            raw = entry["raw"]
            require(isinstance(raw, str), f"{task}/{order}: judge raw must be text")
            raw_bytes = raw.encode("utf-8")
            require(sha256(raw_bytes) == entry["raw_sha256"], f"{task}/{order}: judge raw hash mismatch")
            judgment_hashes[task][order] = entry["raw_sha256"]
            run = entry["run"]
            require(run["model"] == "gpt-5.5" and run["reasoning_effort"] == "high", f"{task}/{order}: judge model mismatch")
            require(run["fresh_context"] is True and run["isolation_level"] == "prompt_trace_only", f"{task}/{order}: judge isolation mismatch")
            require(run["presentation_order"] == ORDERS[order] and run["pair_order"] == PAIR_ORDERS[order], f"{task}/{order}: order mismatch")
            for flag in ATTESTATION_KEYS:
                require(run[flag] is False, f"{task}/{order}: judge isolation flag {flag}")
            require(run["retry_of"] is None and run["status"] == "completed", f"{task}/{order}: judge retry/status mismatch")
            require(run["usage"] == {"input_tokens": None, "output_tokens": None, "total_tokens": None, "available": False}, f"{task}/{order}: unsupported usage claim")

            output = strict_json_bytes(raw_bytes)
            require(isinstance(output, dict), f"{task}/{order}: judge output must be an object")
            require(set(output) == JUDGE_TOP_LEVEL_KEYS, f"{task}/{order}: judge top-level shape mismatch")
            require(output["schema_version"] == "1.0" and output["task_id"] == task, f"{task}/{order}: judge identity mismatch")
            require(output["presentation_order"] == ORDERS[order], f"{task}/{order}: judge output order mismatch")
            require(isinstance(output["candidates"], dict) and set(output["candidates"]) == set(LABELS), f"{task}/{order}: candidate labels mismatch")
            require(isinstance(output["position_or_length_concern"], str), f"{task}/{order}: position/length concern type")
            require(isinstance(output["most_decisive_evidence"], str), f"{task}/{order}: decisive evidence type")
            ranking = output["ranking"]
            require(isinstance(ranking, list) and 1 <= len(ranking) <= len(LABELS), f"{task}/{order}: ranking shape")
            require(all(isinstance(tier, list) and tier for tier in ranking), f"{task}/{order}: ranking tier shape")
            flattened_ranking = [label for tier in ranking for label in tier]
            require(len(flattened_ranking) == len(LABELS) and set(flattened_ranking) == set(LABELS), f"{task}/{order}: ranking must contain each label exactly once")
            label_totals: dict[str, float] = {}
            raw_recomputed_totals: dict[str, float] = {}
            label_dimensions: dict[str, dict[str, float]] = {}
            label_invalid: dict[str, bool] = {}
            reported_totals: dict[str, Any] = {}
            local_mismatches: list[dict[str, Any]] = []
            local_quotes: list[dict[str, Any]] = []
            exclusion_ok = True
            semantic_invalid[task][order] = {}
            semantic_invalid_reasons[task][order] = {}
            for label in LABELS:
                arm = mapping[task][label]
                candidate = output["candidates"][label]
                require(isinstance(candidate, dict) and set(candidate) == JUDGE_CANDIDATE_KEYS, f"{task}/{order}/{label}: candidate shape mismatch")
                reported = candidate["weighted_total"]
                require(
                    isinstance(reported, (int, float)) and not isinstance(reported, bool) and math.isfinite(float(reported)),
                    f"{task}/{order}/{label}: weighted total type",
                )
                require(isinstance(candidate["objective_invalid"], bool), f"{task}/{order}/{label}: objective-invalid type")
                require(isinstance(candidate["invalid_reason"], str), f"{task}/{order}/{label}: invalid-reason type")
                if candidate["objective_invalid"]:
                    require(candidate["invalid_reason"].strip() != "", f"{task}/{order}/{label}: objective-invalid reason is empty")
                require(
                    isinstance(candidate["dimensions"], dict) and set(candidate["dimensions"]) == set(WEIGHTS),
                    f"{task}/{order}/{label}: dimension shape mismatch",
                )
                dim_scores: dict[str, float] = {}
                for dimension in WEIGHTS:
                    cell = candidate["dimensions"][dimension]
                    require(
                        isinstance(cell, dict) and set(cell) == {"candidate_quote", "task_fact", "score"},
                        f"{task}/{order}/{label}/{dimension}: cell shape mismatch",
                    )
                    score = cell["score"]
                    require(isinstance(score, (int, float)) and not isinstance(score, bool), f"{task}/{order}/{label}/{dimension}: score type")
                    require(0 <= score <= 4 and abs(score * 2 - round(score * 2)) < 1e-9, f"{task}/{order}/{label}/{dimension}: score step")
                    require(isinstance(cell["candidate_quote"], str) and isinstance(cell["task_fact"], str) and cell["task_fact"], f"{task}/{order}/{label}/{dimension}: evidence shape")
                    dim_scores[dimension] = float(score)
                    quote = cell["candidate_quote"]
                    if len(quote) > 35:
                        local_quotes.append({"candidate": label, "dimension": dimension, "kind": "over_35_codepoints", "quote": quote, "length": len(quote)})
                    if quote and (answers[task][arm] is None or quote not in answers[task][arm]):
                        local_quotes.append({"candidate": label, "dimension": dimension, "kind": "not_exact_candidate_substring", "quote": quote})
                precheck_invalid = not prechecks[task][arm]["envelope_valid"]
                semantic_hard_invalid = candidate["objective_invalid"] and not precheck_invalid
                effective_invalid = precheck_invalid or semantic_hard_invalid
                semantic_invalid[task][order][arm] = semantic_hard_invalid
                semantic_invalid_reasons[task][order][arm] = candidate["invalid_reason"] if semantic_hard_invalid else ""
                if semantic_hard_invalid:
                    semantic_invalid_cells.append(
                        {
                            "task_id": task,
                            "order": order,
                            "candidate": label,
                            "arm": arm,
                            "reason": candidate["invalid_reason"],
                        }
                    )
                label_invalid[label] = effective_invalid
                recomputed_without_override = weighted_total(candidate["dimensions"])
                raw_recomputed_totals[label] = recomputed_without_override
                total = 0.0 if effective_invalid else recomputed_without_override
                label_totals[label] = total
                effective_dim_scores = {dimension: 0.0 for dimension in WEIGHTS} if effective_invalid else dim_scores
                label_dimensions[label] = effective_dim_scores
                reported_totals[label] = reported
                if abs(float(reported) - recomputed_without_override) > 1e-9:
                    local_mismatches.append({"candidate": label, "reported": reported, "recomputed": clean_number(recomputed_without_override)})
                if precheck_invalid:
                    if candidate["objective_invalid"] is not True or total != 0 or any(value != 0 for value in dim_scores.values()):
                        exclusion_ok = False
                scores[task].setdefault(order, {})[arm] = total
                dimensions[task].setdefault(order, {})[arm] = effective_dim_scores

            require(isinstance(output["pairwise"], list) and len(output["pairwise"]) == 3, f"{task}/{order}: pair count")
            normalized_pairs[task][order] = {}
            reported_pairwise: list[dict[str, str]] = []
            normalized_pairwise: list[dict[str, str]] = []
            local_pair_mismatches: list[dict[str, str]] = []
            for index, (left, right) in enumerate(PAIR_ORDERS[order]):
                pair = output["pairwise"][index]
                require(isinstance(pair, dict) and set(pair) == JUDGE_PAIR_KEYS, f"{task}/{order}: pair shape")
                require(pair["left"] == left and pair["right"] == right, f"{task}/{order}: pair order")
                reported = pair["winner"]
                require(reported in {left, right, "tie"}, f"{task}/{order}: pair winner")
                require(isinstance(pair["reason"], str), f"{task}/{order}: pair reason type")
                expected = normalized_winner(left, right, reported, label_totals, label_invalid)
                reported_pairwise.append({"left": left, "right": right, "winner": reported})
                normalized_pairwise.append({"left": left, "right": right, "winner": expected})
                if reported != expected:
                    local_pair_mismatches.append({"left": left, "right": right, "reported": reported, "normalized": expected})
                left_arm, right_arm = mapping[task][left], mapping[task][right]
                normalized_pairs[task][order][tuple(sorted([left_arm, right_arm]))] = "tie" if expected == "tie" else mapping[task][expected]

            audit = entry["audit"]
            require(audit["parse_status"] == "strict_json" and audit["structure_usable"] is True, f"{task}/{order}: frozen judge audit unusable")
            require(audit["reported_totals"] == reported_totals, f"{task}/{order}: reported-total audit mismatch")
            expected_recomputed = {label: clean_number(raw_recomputed_totals[label]) for label in LABELS}
            require(audit["recomputed_totals"] == expected_recomputed, f"{task}/{order}: recomputed-total audit mismatch")
            require(audit["total_mismatches"] == local_mismatches, f"{task}/{order}: total-mismatch audit changed")
            require(audit["reported_pairwise"] == reported_pairwise, f"{task}/{order}: pairwise audit changed")
            require(audit["normalized_pairwise"] == normalized_pairwise, f"{task}/{order}: normalized pairwise audit changed")
            require(audit["pairwise_mismatches"] == local_pair_mismatches, f"{task}/{order}: pairwise-mismatch audit changed")
            require(audit["quote_deviations"] == local_quotes, f"{task}/{order}: quote audit changed")
            require(exclusion_ok, f"{task}/{order}: precheck invalid was not excluded")
            if not local_mismatches:
                exact_math_judges += 1
            if not local_pair_mismatches:
                exact_pairwise_judges += 1
            precheck_exclusions_correct += int(exclusion_ok)
            for mismatch in local_mismatches:
                mismatch_cells.append({"task_id": task, "order": order, **mismatch})
            for mismatch in local_pair_mismatches:
                pairwise_downgrades.append({"task_id": task, "order": order, **mismatch})
            for deviation in local_quotes:
                quote_deviations.append({"task_id": task, "order": order, **deviation})

    summary = judgments_doc["summary"]
    require(summary["expected_judges"] == 16 and summary["present_judges"] == 16, "judge count changed")
    require(summary["strict_json"] == 16 and summary["structure_usable"] == 16, "judge usability changed")
    require(summary["reported_math_exact"] == exact_math_judges, "judge math summary mismatch")
    require(summary["reported_pairwise_consistent"] == exact_pairwise_judges, "judge pairwise summary mismatch")
    require(summary["precheck_exclusions_correct"] == precheck_exclusions_correct, "judge exclusion summary mismatch")
    require(summary["quote_deviation_count"] == len(quote_deviations), "quote summary mismatch")

    task_results: dict[str, Any] = {}
    pair_results: dict[str, dict[str, Any]] = {"current_vs_no_skill": {}, "current_vs_legacy": {}, "no_skill_vs_legacy": {}}
    order_consistent_tasks = 0
    for task in TASKS:
        mean_scores = {arm: avg([scores[task]["forward"][arm], scores[task]["reverse"][arm]]) for arm in ARMS}
        task_pairs: list[dict[str, Any]] = []
        all_consistent = True
        for left, right in ARM_PAIRS:
            pair_key = tuple(sorted([left, right]))
            decision = consolidate_pair(
                left,
                right,
                normalized_pairs[task]["forward"][pair_key],
                normalized_pairs[task]["reverse"][pair_key],
                scores[task]["forward"],
                scores[task]["reverse"],
            )
            all_consistent = all_consistent and decision["order_consistent"]
            task_pairs.append(decision)
            comparison_name = f"{left}_vs_{right}"
            pair_results[comparison_name][task] = decision
        order_consistent_tasks += int(all_consistent)
        task_results[task] = {
            "precheck_valid": {arm: prechecks[task][arm]["envelope_valid"] for arm in ARMS},
            "semantic_objective_invalid_by_judge": {
                arm: {order: semantic_invalid[task][order][arm] for order in ["forward", "reverse"]}
                for arm in ARMS
            },
            "semantic_invalid_reasons_by_judge": {
                arm: {order: semantic_invalid_reasons[task][order][arm] for order in ["forward", "reverse"]}
                for arm in ARMS
            },
            "answer_codepoints": {arm: prechecks[task][arm]["answer_codepoints"] for arm in ARMS},
            "scores": {
                arm: {
                    "forward": clean_number(scores[task]["forward"][arm]),
                    "reverse": clean_number(scores[task]["reverse"][arm]),
                    "two_judge_mean": mean_scores[arm],
                }
                for arm in ARMS
            },
            "current_deltas": {
                "vs_no_skill": clean_number(float(mean_scores["current"]) - float(mean_scores["no_skill"])),
                "vs_legacy": clean_number(float(mean_scores["current"]) - float(mean_scores["legacy"])),
            },
            "pairs": task_pairs,
            "all_three_pairs_order_consistent": all_consistent,
        }

    arm_summary: dict[str, Any] = {}
    for arm in ARMS:
        task_means = [float(task_results[task]["scores"][arm]["two_judge_mean"]) for task in TASKS]
        valid_task_means = [
            float(task_results[task]["scores"][arm]["two_judge_mean"])
            for task in TASKS
            if prechecks[task][arm]["envelope_valid"]
        ]
        arm_summary[arm] = {
            "precheck_valid_tasks": sum(prechecks[task][arm]["envelope_valid"] for task in TASKS),
            "semantic_objective_invalid_judge_orders": sum(
                semantic_invalid[task][order][arm]
                for task in TASKS
                for order in ["forward", "reverse"]
            ),
            "task_score_median": med(task_means),
            "task_score_mean": avg(task_means),
            "valid_task_score_median": med(valid_task_means),
            "valid_task_score_mean": avg(valid_task_means),
        }

    comparisons: dict[str, Any] = {}
    for baseline in ["no_skill", "legacy"]:
        name = f"current_vs_{baseline}"
        deltas = [
            float(task_results[task]["scores"]["current"]["two_judge_mean"])
            - float(task_results[task]["scores"][baseline]["two_judge_mean"])
            for task in TASKS
        ]
        status_counts = {key: 0 for key in ["strict_win", "strict_loss", "low_confidence_lean", "low_confidence_against", "tie_low_confidence"]}
        for decision in pair_results[name].values():
            status_counts[decision["status_from_left"]] += 1
        comparisons[name] = {
            "per_task_delta": {task: clean_number(delta) for task, delta in zip(TASKS, deltas)},
            "median_delta": med(deltas),
            "mean_delta": avg(deltas),
            "pair_outcomes": {task: pair_results[name][task] for task in TASKS},
            "outcome_counts": status_counts,
        }

    valid_pair_sensitivity: dict[str, Any] = {
        "status": "post_run_descriptive_not_preregistered",
        "definition": "A task is eligible when both arms have envelope-valid candidates and neither arm is judge-marked semantic objective-invalid in either reading order. Statistics retain the task as the unit and do not replace the preregistered main result.",
        "comparisons": {},
    }
    for baseline in ["no_skill", "legacy"]:
        name = f"current_vs_{baseline}"
        eligible_tasks = [
            task
            for task in TASKS
            if prechecks[task]["current"]["envelope_valid"]
            and prechecks[task][baseline]["envelope_valid"]
            and not any(
                semantic_invalid[task][order][arm]
                for order in ["forward", "reverse"]
                for arm in ["current", baseline]
            )
        ]
        eligible_deltas = [float(comparisons[name]["per_task_delta"][task]) for task in eligible_tasks]
        eligible_outcome_counts = {
            key: 0
            for key in ["strict_win", "strict_loss", "low_confidence_lean", "low_confidence_against", "tie_low_confidence"]
        }
        for task in eligible_tasks:
            eligible_outcome_counts[pair_results[name][task]["status_from_left"]] += 1
        valid_pair_sensitivity["comparisons"][name] = {
            "eligible_tasks": eligible_tasks,
            "eligible_task_count": len(eligible_tasks),
            "median_delta": med(eligible_deltas) if eligible_deltas else None,
            "per_task_delta": {task: clean_number(comparisons[name]["per_task_delta"][task]) for task in eligible_tasks},
            "outcome_counts": eligible_outcome_counts,
        }

    dimension_results: dict[str, Any] = {}
    for baseline in ["no_skill", "legacy"]:
        comparison = {}
        for dimension in WEIGHTS:
            deltas = []
            for task in TASKS:
                current_score = statistics.fmean([dimensions[task][order]["current"][dimension] for order in ["forward", "reverse"]])
                baseline_score = statistics.fmean([dimensions[task][order][baseline][dimension] for order in ["forward", "reverse"]])
                deltas.append(current_score - baseline_score)
            comparison[dimension] = {
                "median_delta_on_0_to_4_scale": med(deltas),
                "per_task_delta": {task: clean_number(delta) for task, delta in zip(TASKS, deltas)},
            }
        dimension_results[f"current_vs_{baseline}"] = comparison

    # Within-task centering prevents easy tasks from creating a spurious length/score relation.
    centered_lengths: list[float] = []
    centered_scores: list[float] = []
    for task in TASKS:
        valid_arms = [arm for arm in ARMS if prechecks[task][arm]["envelope_valid"]]
        lengths = [float(prechecks[task][arm]["answer_codepoints"]) for arm in valid_arms]
        task_scores = [float(task_results[task]["scores"][arm]["two_judge_mean"]) for arm in valid_arms]
        length_mean = statistics.fmean(lengths)
        score_mean = statistics.fmean(task_scores)
        centered_lengths.extend(length - length_mean for length in lengths)
        centered_scores.extend(score - score_mean for score in task_scores)
    length_score_correlation = pearson(centered_lengths, centered_scores)
    resolved_valid_pairs = 0
    longer_answer_wins = 0
    for pair_name, pair_group in pair_results.items():
        left, right = pair_name.split("_vs_")
        for task, decision in pair_group.items():
            if not prechecks[task][left]["envelope_valid"] or not prechecks[task][right]["envelope_valid"]:
                continue
            favored = decision["favored_arm"]
            if favored is None:
                continue
            left_length = prechecks[task][left]["answer_codepoints"]
            right_length = prechecks[task][right]["answer_codepoints"]
            if left_length == right_length:
                continue
            resolved_valid_pairs += 1
            longer = left if left_length > right_length else right
            longer_answer_wins += int(favored == longer)
    longer_win_rate = longer_answer_wins / resolved_valid_pairs if resolved_valid_pairs else 0.0
    descriptive_length_alert = abs(length_score_correlation) >= 0.50 and resolved_valid_pairs >= 6 and longer_win_rate >= 0.75

    current_leakage_hard_fail = any(prechecks[task]["current"]["leakage_hits"] for task in TASKS)
    current_semantic_constraint_hard_fail = any(
        semantic_invalid[task][order]["current"]
        for task in TASKS
        for order in ["forward", "reverse"]
    )
    current_hard_fail = current_leakage_hard_fail or current_semantic_constraint_hard_fail
    # The public preregistration required no unresolved length confound, but did
    # not preregister a numeric resolution rule. The post-run diagnostic below
    # therefore cannot establish that this part of the gate passed.
    length_confounding_resolved = False
    gate_checks = {
        "current_valid_at_least_7_of_8_and_no_leakage_or_safety_hard_fail": {
            "actual_valid": arm_summary["current"]["precheck_valid_tasks"],
            "leakage_hard_fail": current_leakage_hard_fail,
            "semantic_constraint_or_safety_hard_fail": current_semantic_constraint_hard_fail,
            "ordinary_envelope_invalid_is_not_automatically_a_hard_fail": True,
            "hard_fail": current_hard_fail,
            "pass": arm_summary["current"]["precheck_valid_tasks"] >= 7 and not current_hard_fail,
        },
        "current_strict_wins_vs_no_skill_at_least_7_of_8": {
            "actual": comparisons["current_vs_no_skill"]["outcome_counts"]["strict_win"],
            "pass": comparisons["current_vs_no_skill"]["outcome_counts"]["strict_win"] >= 7,
        },
        "current_strict_wins_vs_legacy_at_least_7_of_8": {
            "actual": comparisons["current_vs_legacy"]["outcome_counts"]["strict_win"],
            "pass": comparisons["current_vs_legacy"]["outcome_counts"]["strict_win"] >= 7,
        },
        "median_total_delta_at_least_plus_5_vs_both": {
            "actual": {
                "no_skill": comparisons["current_vs_no_skill"]["median_delta"],
                "legacy": comparisons["current_vs_legacy"]["median_delta"],
            },
            "pass": comparisons["current_vs_no_skill"]["median_delta"] >= 5 and comparisons["current_vs_legacy"]["median_delta"] >= 5,
        },
        "key_dimension_median_deltas_nonnegative_vs_both": {
            "dimensions": KEY_DIMENSIONS,
            "actual": {
                baseline: {
                    dimension: dimension_results[f"current_vs_{baseline}"][dimension]["median_delta_on_0_to_4_scale"]
                    for dimension in KEY_DIMENSIONS
                }
                for baseline in ["no_skill", "legacy"]
            },
            "pass": all(
                dimension_results[f"current_vs_{baseline}"][dimension]["median_delta_on_0_to_4_scale"] >= 0
                for baseline in ["no_skill", "legacy"]
                for dimension in KEY_DIMENSIONS
            ),
        },
        "at_least_7_of_8_tasks_order_consistent_and_length_confounding_resolved": {
            "actual_order_consistent_tasks": order_consistent_tasks,
            "post_run_descriptive_length_alert": descriptive_length_alert,
            "length_confounding_resolved": length_confounding_resolved,
            "length_resolution_rule_publicly_preregistered": False,
            "pass": order_consistent_tasks >= 7 and length_confounding_resolved,
        },
    }
    gate_pass = all(item["pass"] for item in gate_checks.values())

    result = {
        "schema_version": "1.0",
        "benchmark_id": prerun["evaluation_id"],
        "aggregation_version": "1.0",
        "status": "complete",
        "evidence_ceiling": prerun["evidence_ceiling"],
        "integrity": {
            "all_checks_passed": True,
            "preregistered_commitments_verified": verified_files,
            "candidate_raw_hashes_verified": candidate_hashes,
            "judgment_raw_hashes_verified": judgment_hashes,
            "candidate_source_freeze": {
                "declared_sha256": candidates_doc["source_freeze_sha256"],
                "verification": "not_independently_verifiable_from_public_release; source manifest is not published",
            },
            "judgment_source_freeze": {
                "declared_sha256": judgments_doc["source_freeze_sha256"],
                "verification": "not_independently_verifiable_from_public_release; source manifest is not published",
            },
            "legacy_bundle": {
                "declared_commit_and_hashes_match_preregistration": True,
                "historical_bytes_verified_by_this_evaluator": False,
            },
            "candidate_outputs_verified": 24,
            "judge_outputs_verified": 16,
        },
        "run_accounting": {
            "candidate_runs": 24,
            "candidate_precheck_valid": valid_count,
            "candidate_precheck_invalid": 24 - valid_count,
            "judge_runs": 16,
            "judge_strict_json_and_usable": 16,
            "candidate_quality_retries": 0,
            "judge_quality_retries": 0,
            "judge_semantic_objective_invalid_cells": len(semantic_invalid_cells),
            "isolation_level": "prompt_trace_only",
        },
        "arm_summary": arm_summary,
        "tasks": task_results,
        "comparisons": comparisons,
        "valid_pair_sensitivity": valid_pair_sensitivity,
        "dimension_deltas": dimension_results,
        "order_consistency": {
            "definition": "all three normalized arm-pair outcomes match across forward and reverse readings",
            "consistent_tasks": order_consistent_tasks,
            "total_tasks": 8,
            "per_task": {task: task_results[task]["all_three_pairs_order_consistent"] for task in TASKS},
        },
        "length_diagnostic": {
            "definition": "Pearson correlation after centering valid candidate lengths and two-judge mean scores within each task; alert also requires longer-answer wins >=75% of >=6 resolved valid-valid pairs",
            "status": "post_run_descriptive_not_publicly_preregistered",
            "can_resolve_preregistered_length_confounding_gate": False,
            "within_task_centered_pearson_r": clean_number(length_score_correlation),
            "resolved_valid_valid_pairs": resolved_valid_pairs,
            "longer_answer_wins": longer_answer_wins,
            "longer_answer_win_rate": clean_number(longer_win_rate),
            "descriptive_alert": descriptive_length_alert,
            "interpretation": "No descriptive alert is not evidence that length confounding was resolved; the numeric alert rule was not in the public preregistration.",
        },
        "judge_audit": {
            "reported_math_exact_judges": exact_math_judges,
            "reported_math_inexact_judges": 16 - exact_math_judges,
            "reported_total_mismatch_cell_count": len(mismatch_cells),
            "reported_total_mismatch_cells": mismatch_cells,
            "reported_pairwise_fully_consistent_judges": exact_pairwise_judges,
            "reported_pairwise_downgrade_count": len(pairwise_downgrades),
            "reported_pairwise_downgrades": pairwise_downgrades,
            "quote_deviation_count": len(quote_deviations),
            "quote_deviation_kinds": {
                "not_exact_candidate_substring": sum(item["kind"] == "not_exact_candidate_substring" for item in quote_deviations),
                "over_35_codepoints": sum(item["kind"] == "over_35_codepoints" for item in quote_deviations),
            },
            "quote_deviations": quote_deviations,
            "semantic_objective_invalid_valid_envelope_cells": semantic_invalid_cells,
            "authoritative_policy": "Totals are recomputed from frozen dimensions. In each order, a reported pair winner counts only when it agrees with the recomputed score direction and leads by at least 5/100; otherwise the pair is normalized to tie. A precheck-invalid or judge-marked objective-invalid candidate scores zero and automatically loses to a valid candidate in that order.",
            "policy_provenance_limitation": "The zero-score/automatic-loss handling for invalid candidates was recorded in the nonpublic run aggregation notes but was not stated verbatim in the public preregistration.",
            "evidence_limitation": "quote deviations and post-prereg arithmetic normalization reduce confidence in the subjective evidence even though every change is deterministic and raw outputs remain public",
        },
        "advancement_gate": {
            "verdict": "pass_for_confirmatory_expansion" if gate_pass else "does_not_pass_confirmatory_expansion_gate",
            "all_checks_pass": gate_pass,
            "checks": gate_checks,
            "interpretation": "A failure means this frozen development set did not clear the preregistered expansion gate; it does not establish that the Skill is ineffective.",
        },
        "runtime_verdict": "runtime_savings_not_supported",
        "limitations": [
            "Eight paired development tasks and one candidate per arm per task are exploratory, not a general advantage proof.",
            "Candidate and judge models differ but remain within one provider family.",
            "Isolation is prompt_trace_only; no operating-system-call forensic sandbox was available.",
            "Comparable token and wall-clock usage were unavailable, so runtime savings are not inferred.",
            "Twenty-eight quote deviations and judge arithmetic mismatches require deterministic normalization and weaken evidentiary confidence.",
            "The numeric length-alert rule is a post-run descriptive diagnostic, not a publicly preregistered resolution rule; length confounding therefore remains unresolved for the advancement gate.",
            "The candidate and judgment source_freeze hashes point to unpublished working manifests and cannot be independently verified from the public release alone.",
            "Legacy bundle commit and file hashes are checked as declared metadata against the preregistration, but this evaluator does not verify the historical legacy file bytes.",
            "The invalid-candidate zero-score/automatic-loss aggregation rule was not stated verbatim in the public preregistration.",
            "The task pack and mapping are now public and cannot serve as a future blind holdout without replacement tasks.",
        ],
    }
    return result


def encoded(result: dict[str, Any]) -> bytes:
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", metavar="PATH", help="write the recomputed result")
    group.add_argument("--check", metavar="PATH", help="verify an existing result byte-for-byte")
    args = parser.parse_args()
    try:
        result = evaluate()
        data = encoded(result)
        if args.write:
            output = Path(args.write)
            if not output.is_absolute():
                output = HERE / output
            output.write_bytes(data)
            print(f"WROTE {output.name} ({sha256(data)})")
        elif args.check:
            expected = Path(args.check)
            if not expected.is_absolute():
                expected = HERE / expected
            actual = expected.read_bytes()
            require(actual == data, f"result mismatch: expected recomputed SHA-256 {sha256(data)}, found {sha256(actual)}")
            print(f"PASS {result['benchmark_id']}: {expected.name} = {sha256(data)}")
        else:
            sys.stdout.buffer.write(data)
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
