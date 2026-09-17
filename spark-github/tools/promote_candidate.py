from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from tools.check_evaluation import EvaluationError, load_evaluation
from tools.reef_tree import load_tree


class PromotionError(ValueError):
    pass


def _copy_json(source: Path, destination: Path) -> None:
    data = json.loads(source.read_text(encoding="utf-8"))
    destination.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def promote_candidate(
    repo_root: str | Path,
    harness: str,
    candidate_id: str,
    evaluation_path: str | Path,
    release_id: str,
) -> Path:
    root = Path(repo_root)
    current = root / "harnesses" / harness / "tree.json"
    candidate = root / "candidates" / harness / candidate_id / "tree.json"
    evaluation_file = Path(evaluation_path)

    if not current.exists():
        raise PromotionError(f"current harness tree not found: {current}")
    if not candidate.exists():
        raise PromotionError(f"candidate tree not found: {candidate}")

    # Validate both JSON trees using the same portable REEF vocabulary used by export.
    load_tree(current)
    load_tree(candidate)

    try:
        evaluation = load_evaluation(evaluation_file)
    except EvaluationError as exc:
        raise PromotionError(str(exc)) from exc
    if evaluation.harness != harness:
        raise PromotionError(f"evaluation harness {evaluation.harness!r} does not match {harness!r}")
    if evaluation.candidate_id != candidate_id:
        raise PromotionError(
            f"evaluation candidate_id {evaluation.candidate_id!r} does not match {candidate_id!r}"
        )
    if evaluation.decision != "PROMOTE":
        raise PromotionError(f"evaluation decision is {evaluation.decision}, not PROMOTE")
    if not release_id or any(ch in release_id for ch in "/\\"):
        raise PromotionError("release_id must be a non-empty path-safe identifier")

    release_dir = root / "releases" / harness / release_id
    if release_dir.exists():
        raise PromotionError(f"release already exists: {release_dir}")
    release_dir.mkdir(parents=True)

    shutil.copy2(current, release_dir / "previous-tree.json")
    _copy_json(candidate, release_dir / "tree.json")
    _copy_json(evaluation_file, release_dir / "evaluation.json")
    release_metadata = {
        "format": "reef-spark-release-v1",
        "harness": harness,
        "candidate_id": candidate_id,
        "release_id": release_id,
        "evaluated_by": evaluation.evaluated_by,
        "cases_total": evaluation.cases_total,
        "current_passed": evaluation.current_passed,
        "candidate_passed": evaluation.candidate_passed,
    }
    (release_dir / "release.json").write_text(
        json.dumps(release_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _copy_json(candidate, current)
    return release_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote one evaluated Spark/REEF candidate.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--harness", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--evaluation", required=True, type=Path)
    parser.add_argument("--release-id", required=True)
    args = parser.parse_args()
    path = promote_candidate(args.repo_root, args.harness, args.candidate_id, args.evaluation, args.release_id)
    print(path)


if __name__ == "__main__":
    main()
