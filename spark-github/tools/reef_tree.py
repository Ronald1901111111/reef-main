from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

REEF_NODE_KINDS = {
    "config",
    "rules",
    "agent_command",
    "skill",
    "code_extension",
    "native_tool",
    "native_hook",
    "native_graph",
    "native_agent",
    "native_loop",
}

SPARK_EXPORTABLE_KINDS = {"config", "rules", "agent_command", "skill"}
SPARK_EXECUTABLE_BLOCKED_KINDS = REEF_NODE_KINDS - SPARK_EXPORTABLE_KINDS


class TreeValidationError(ValueError):
    pass


class SparkUnsupportedNodeError(TreeValidationError):
    pass


@dataclass(frozen=True)
class Entry:
    id: str
    kind: str
    config: dict[str, Any]


def _require_nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TreeValidationError(f"{where} must be a non-empty string")
    return value


def _validate_named_node(entry_id: str, config: dict[str, Any]) -> None:
    name = config.get("name")
    if not isinstance(name, str) or not name:
        raise TreeValidationError(f"entry {entry_id!r} requires config.name")
    if not NAME_PATTERN.fullmatch(name):
        raise TreeValidationError(f"entry {entry_id!r} config.name {name!r} must match {NAME_PATTERN.pattern}")


def _validate_entry(entry: Entry) -> None:
    config = entry.config
    if entry.kind == "rules":
        _require_nonempty_string(config.get("text"), f"entry {entry.id!r} rules.text")
    elif entry.kind in {"skill", "agent_command"}:
        _validate_named_node(entry.id, config)
        _require_nonempty_string(config.get("text"), f"entry {entry.id!r} {entry.kind}.text")
    elif entry.kind == "config":
        data = config.get("data", {})
        if not isinstance(data, dict):
            raise TreeValidationError(f"entry {entry.id!r} config.data must be an object")
        target = config.get("target", "primary")
        _require_nonempty_string(target, f"entry {entry.id!r} config.target")
    else:
        # Executable/native kinds are intentionally not reimplemented here.
        # They are valid REEF vocabulary but Spark export refuses them later.
        name = config.get("name")
        if name is not None:
            _validate_named_node(entry.id, config)


def load_tree(path: str | Path) -> list[Entry]:
    tree_path = Path(path)
    try:
        data = json.loads(tree_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TreeValidationError(f"cannot read {tree_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise TreeValidationError(f"{tree_path} is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise TreeValidationError("tree.json must contain a JSON array")

    seen: set[str] = set()
    entries: list[Entry] = []
    for index, raw in enumerate(data):
        if not isinstance(raw, dict):
            raise TreeValidationError(f"entry {index} must be an object")
        entry_id = _require_nonempty_string(raw.get("id"), f"entry {index}.id")
        if entry_id in seen:
            raise TreeValidationError(f"duplicate entry id {entry_id!r}")
        seen.add(entry_id)

        kind = _require_nonempty_string(raw.get("name"), f"entry {entry_id!r}.name")
        if kind not in REEF_NODE_KINDS:
            raise TreeValidationError(f"entry {entry_id!r} uses unknown REEF node kind {kind!r}")

        config = raw.get("config")
        if not isinstance(config, dict):
            raise TreeValidationError(f"entry {entry_id!r} config must be an object")

        entry = Entry(id=entry_id, kind=kind, config=dict(config))
        _validate_entry(entry)
        entries.append(entry)
    return entries


def validate_spark_exportable(entries: list[Entry]) -> None:
    blocked = sorted({entry.kind for entry in entries if entry.kind in SPARK_EXECUTABLE_BLOCKED_KINDS})
    if blocked:
        joined = ", ".join(blocked)
        raise SparkUnsupportedNodeError(
            f"Spark export refuses executable REEF node kinds: {joined}. "
            "Use REEF native/headless evaluation for those nodes or remove them from the Spark target."
        )
