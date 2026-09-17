from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.package_spark import export_spark_bundle


def package_repository(repo_root: str | Path, out_dir: str | Path) -> list[Path]:
    root = Path(repo_root)
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    produced: list[Path] = []

    harness_root = root / "harnesses"
    if harness_root.exists():
        for tree in sorted(harness_root.glob("*/tree.json")):
            name = tree.parent.name
            target = out / "harnesses" / name
            export_spark_bundle(tree, name, target)
            produced.append(target)

    candidate_root = root / "candidates"
    if candidate_root.exists():
        for tree in sorted(candidate_root.glob("*/*/tree.json")):
            harness = tree.parents[1].name
            candidate_id = tree.parent.name
            name = f"{harness}-candidate-{candidate_id}"
            target = out / "candidates" / harness / candidate_id
            export_spark_bundle(tree, name, target)
            produced.append(target)
    return produced


def main() -> None:
    parser = argparse.ArgumentParser(description="Package every current and candidate REEF tree in a repository.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    produced = package_repository(args.repo_root, args.out)
    for path in produced:
        print(path)


if __name__ == "__main__":
    main()
