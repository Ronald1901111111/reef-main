from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class Evaluation:
    harness: str
    candidate_id: str
    decision: str
    evaluated_by: str
    cases_total: int
    current_passed: int
    candidate_passed: int
    notes: str
    raw: dict[str, Any]


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"evaluation requires non-empty string {key!r}")
    return value


def _require_nonnegative_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvaluationError(f"evaluation requires non-negative integer {key!r}")
    return value


def load_evaluation(path: str | Path) -> Evaluation:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvaluationError(f"cannot read evaluation {p}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"evaluation {p} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise EvaluationError("evaluation must be a JSON object")
    if data.get("format") != "reef-spark-evaluation-v1":
        raise EvaluationError("evaluation format must be 'reef-spark-evaluation-v1'")
    harness = _require_str(data, "harness")
    candidate_id = _require_str(data, "candidate_id")
    decision = _require_str(data, "decision").upper()
    if decision not in {"PROMOTE", "REJECT"}:
        raise EvaluationError("evaluation decision must be PROMOTE or REJECT")
    evaluated_by = _require_str(data, "evaluated_by")
    cases_total = _require_nonnegative_int(data, "cases_total")
    current_passed = _require_nonnegative_int(data, "current_passed")
    candidate_passed = _require_nonnegative_int(data, "candidate_passed")
    if current_passed > cases_total or candidate_passed > cases_total:
        raise EvaluationError("passed counts cannot exceed cases_total")
    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise EvaluationError("evaluation notes must be a string")
    return Evaluation(
        harness=harness,
        candidate_id=candidate_id,
        decision=decision,
        evaluated_by=evaluated_by,
        cases_total=cases_total,
        current_passed=current_passed,
        candidate_passed=candidate_passed,
        notes=notes,
        raw=dict(data),
    )
