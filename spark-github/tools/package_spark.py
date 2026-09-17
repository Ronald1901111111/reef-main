from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from tools.reef_tree import Entry, load_tree, validate_spark_exportable

_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _normalize_text(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def _skill_text(name: str, text: str, *, description: str) -> str:
    normalized = _normalize_text(text)
    if normalized.startswith("---\n"):
        return normalized
    return f"---\nname: {name}\ndescription: {description}\n---\n{normalized}"


def _command_text(name: str, text: str) -> str:
    body = _normalize_text(text)
    return (
        f"---\nname: {name}\ndescription: Human-invoked command exported from a REEF agent_command node.\n---\n"
        "# HUMAN-INVOCATION POLICY\n\n"
        "This command is intended to be started by the human. Do not auto-invoke it merely because it appears relevant. "
        "Gemini Spark may not enforce Claude/Codex invocation metadata, so this policy is instructional.\n\n"
        f"{body}"
    )


def _controller_text(harness: str, rules: list[str], skills: list[str], commands: list[str]) -> str:
    rule_text = "\n\n".join(rule.strip() for rule in rules if rule.strip()) or "No REEF rules nodes were present."
    skills_text = "\n".join(f"- `{name}`" for name in skills) or "- none"
    commands_text = "\n".join(f"- `{name}` (human-invoked)" for name in commands) or "- none"
    return _normalize_text(
        f"""---
name: {harness}-controller
description: Coordinates the Spark-exported REEF harness {harness}.
---
# {harness} controller

This skill is the Spark compatibility controller for a REEF harness tree. The separately exported component skills must be installed independently when they are needed.

## Global rules

{rule_text}

## Component skills

{skills_text}

## Human-invoked commands

{commands_text}

## Runtime truthfulness

REEF `config` nodes are source metadata only in this Spark export and are not claimed to alter Spark model/runtime settings. Executable REEF node kinds are refused by the exporter rather than simulated.
"""
    )


def _write_zip(path: Path, files: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, _normalize_text(files[name]).encode("utf-8"))


def _collect(entries: list[Entry]):
    rules: list[str] = []
    skills: dict[str, str] = {}
    commands: dict[str, str] = {}
    configs: list[dict] = []

    for entry in entries:
        if entry.kind == "rules":
            rules.append(str(entry.config["text"]))
        elif entry.kind == "skill":
            name = str(entry.config["name"])
            if name in skills or name in commands:
                raise ValueError(f"name collision for Spark package {name!r}")
            skills[name] = str(entry.config["text"])
        elif entry.kind == "agent_command":
            name = str(entry.config["name"])
            if name in commands or name in skills:
                raise ValueError(f"name collision for Spark package {name!r}")
            commands[name] = str(entry.config["text"])
        elif entry.kind == "config":
            configs.append({"id": entry.id, **entry.config})
    return rules, skills, commands, configs


def export_spark_bundle(tree_path: str | Path, harness: str, out_dir: str | Path) -> Path:
    entries = load_tree(tree_path)
    validate_spark_exportable(entries)
    rules, skills, commands, configs = _collect(entries)

    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    (out / "controller").mkdir(parents=True, exist_ok=True)
    (out / "skills").mkdir(parents=True, exist_ok=True)
    (out / "commands").mkdir(parents=True, exist_ok=True)

    controller = _controller_text(harness, rules, sorted(skills), sorted(commands))
    _write_zip(out / "controller" / f"{harness}-controller.zip", {"SKILL.md": controller})

    for name in sorted(skills):
        _write_zip(
            out / "skills" / f"{name}.zip",
            {"SKILL.md": _skill_text(name, skills[name], description=f"REEF-exported Spark skill {name}.")},
        )

    for name in sorted(commands):
        _write_zip(out / "commands" / f"{name}.zip", {"SKILL.md": _command_text(name, commands[name])})

    manifest = {
        "format": "reef-spark-bundle-v1",
        "harness": harness,
        "controller": f"controller/{harness}-controller.zip",
        "skills": sorted(skills),
        "commands": sorted(commands),
        "source_configs": configs,
        "warnings": [
            "REEF config nodes are preserved as source information only; Spark runtime settings are not modified by this exporter."
        ] if configs else [],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a portable REEF tree to a Gemini Spark skill bundle.")
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    export_spark_bundle(args.tree, args.name, args.out)
    print(args.out)


if __name__ == "__main__":
    main()
