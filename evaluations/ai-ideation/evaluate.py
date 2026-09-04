from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


BASELINE_COMMIT = "3278710dc8a141a5ecb9a7651c86ea2b9da631e6"
BASELINE_SKILL_SHA256 = "14b6fd6a1e831baf92853bb6f9e9c1fa1b473bc2f1343548522daf9350100fb0"
BASELINE_AI_RESEARCH_SHA256 = "138c0a49eedfa9159e669e4067360ccaa544eee32a20c77b596ec6012b942e8c"
BASELINE_PAYLOAD_BYTES = 25_062

HANDOFF_FIELDS = (
    "IDEA_ID",
    "OBS_OR_GAP",
    "Q",
    "HYP",
    "RIVAL",
    "PRED",
    "FALSIFIER",
    "CORE",
    "BOUNDARY",
    "CHEAPEST_TEST",
    "EVIDENCE_STATE",
    "NOVELTY_STATE",
)

NOVELTY_STATES = (
    "not-searched",
    "incomplete-search",
    "not-located-within-boundary",
    "near-neighbor-found",
    "overlap-found",
)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def load_json_strict(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise ValueError("result root must be an object")
    return value


def read_utf8(path: Path) -> tuple[bytes, str]:
    data = path.read_bytes()
    return data, data.decode("utf-8", errors="strict")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_result(repo: Path) -> dict[str, Any]:
    skill_data, skill = read_utf8(repo / "SKILL.md")
    idea_data, idea = read_utf8(repo / "references" / "ai-ideation.md")
    research_data, research = read_utf8(repo / "references" / "ai-research.md")

    pure_idea_bytes = len(skill_data) + len(idea_data)
    full_research_bytes = len(skill_data) + len(research_data)
    sequential_transition_bytes = len(skill_data) + len(idea_data) + len(research_data)
    reduction_bytes = BASELINE_PAYLOAD_BYTES - pure_idea_bytes
    reduction_percent = round(reduction_bytes / BASELINE_PAYLOAD_BYTES * 100, 6)
    sequential_change_percent = round(
        (sequential_transition_bytes - BASELINE_PAYLOAD_BYTES) / BASELINE_PAYLOAD_BYTES * 100,
        6,
    )

    gates = {
        "pure_idea_routes_to_light_reference": all(
            marker in skill
            for marker in (
                "[AI idea 快速闭环](references/ai-ideation.md)",
                "不要预载完整实验流程",
            )
        ),
        "selected_idea_routes_to_full_research": all(
            marker in skill
            for marker in (
                "[AI 科研闭环](references/ai-research.md)",
                "只把入选候选的最小保真包交给科研闭环",
            )
        ),
        "research_accepts_handoff_and_routes_back": all(
            marker in research
            for marker in (
                "IDEA_ID, OBS_OR_GAP, Q, HYP, RIVAL, PRED, FALSIFIER, CORE, BOUNDARY, CHEAPEST_TEST, EVIDENCE_STATE, NOVELTY_STATE",
                "[AI idea 快速闭环](ai-ideation.md)",
                "一个 Falsifier 和一个实验",
            )
        ),
        "ideation_quality_invariants_present": all(
            marker in idea
            for marker in (
                "重构问题",
                "机制指纹",
                "竞争解释",
                "反平庸",
                "普通资源的短板",
                "saturation",
            )
        ),
        "handoff_fields_complete": all(field in idea for field in HANDOFF_FIELDS),
        "bounded_novelty_states_complete": all(state in idea for state in NOVELTY_STATES),
        "legacy_generation_heading_absent": "## 2. 用控制缺口生成更有价值的 idea" not in research,
        "pure_idea_payload_reduction_at_least_30_percent": reduction_percent >= 30.0,
        "full_research_payload_not_larger_than_baseline": full_research_bytes <= BASELINE_PAYLOAD_BYTES,
    }

    passed = all(gates.values())
    return {
        "schema_version": "1.0-public",
        "evaluation_id": "CEC-AIIdeation-Structure-1",
        "evaluation_date": "2026-09-04",
        "scope": "deterministic progressive-disclosure and static instruction-payload regression",
        "baseline": {
            "source_commit": BASELINE_COMMIT,
            "skill_sha256": BASELINE_SKILL_SHA256,
            "ai_research_sha256": BASELINE_AI_RESEARCH_SHA256,
            "pure_ai_instruction_files": ["SKILL.md", "references/ai-research.md"],
            "utf8_bytes": BASELINE_PAYLOAD_BYTES,
        },
        "current": {
            "skill_sha256": sha256(skill_data),
            "ai_ideation_sha256": sha256(idea_data),
            "ai_research_sha256": sha256(research_data),
            "pure_idea_instruction_files": ["SKILL.md", "references/ai-ideation.md"],
            "pure_idea_utf8_bytes": pure_idea_bytes,
            "full_research_instruction_files": ["SKILL.md", "references/ai-research.md"],
            "full_research_utf8_bytes": full_research_bytes,
            "same_context_sequential_files": [
                "SKILL.md",
                "references/ai-ideation.md",
                "references/ai-research.md",
            ],
            "same_context_sequential_utf8_bytes": sequential_transition_bytes,
            "same_context_sequential_vs_baseline_percent": sequential_change_percent,
            "pure_idea_reduction_bytes": reduction_bytes,
            "pure_idea_reduction_percent": reduction_percent,
        },
        "gates": gates,
        "gate_summary": {
            "passed": sum(gates.values()),
            "total": len(gates),
            "status": "PASS" if passed else "FAIL",
        },
        "verdict": {
            "progressive_disclosure_structurally_verified": passed,
            "static_instruction_payload_reduction_observed": reduction_percent >= 30.0,
            "behavioral_idea_quality_advantage_supported": False,
            "runtime_token_savings_supported": False,
            "same_context_end_to_end_payload_reduction_observed": sequential_transition_bytes
            < BASELINE_PAYLOAD_BYTES,
        },
        "limitations": [
            "UTF-8 bytes are a static instruction-payload proxy, not model input tokens, cache behavior, latency, money or total runtime cost.",
            "Marker gates verify release structure, not semantic compliance by an agent.",
            "The public task is not blind and cannot establish better ideas or research outcomes.",
            "If one context retains both references while moving from ideation to implementation, the cumulative static payload is larger than the old monolithic path.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, help="compare the derived result with a frozen JSON file")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    repo = Path(__file__).resolve().parents[2]
    result = build_result(repo)
    if args.check is not None:
        expected_path = args.check if args.check.is_absolute() else Path.cwd() / args.check
        expected = load_json_strict(expected_path)
        if expected != result:
            print("FAIL: frozen result does not match current release structure", file=sys.stderr)
            return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["gate_summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
