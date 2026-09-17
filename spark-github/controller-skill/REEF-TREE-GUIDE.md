# REEF Tree Guide for Spark

REEF represents a harness as a flat entry tree. Each entry has:

```json
{
  "id": "stable-entry-id",
  "name": "skill",
  "config": {}
}
```

## Spark-exportable kinds

### rules

```json
{"id":"rules-1","name":"rules","config":{"text":"Global instruction."}}
```

All `rules` text is folded into the exported controller skill.

### skill

```json
{"id":"skill-1","name":"skill","config":{"name":"research","text":"# Research\n..."}}
```

Each skill becomes an independently installable ZIP with `SKILL.md` at its root.

### agent_command

```json
{"id":"cmd-1","name":"agent_command","config":{"name":"review","text":"Review the candidate."}}
```

Each command becomes a separate Spark skill ZIP containing a human-invocation policy. Spark may not enforce the same user-only invocation metadata as Claude/Codex, so this is an instructional compatibility layer.

### config

Config nodes are preserved in the bundle manifest as source information. The exporter does not claim they change Spark runtime/model settings.

## Refused for Spark export v1

- `code_extension`
- `native_tool`
- `native_hook`
- `native_graph`
- `native_agent`
- `native_loop`

These kinds imply executable behavior that an uploaded Spark skill ZIP cannot faithfully reproduce. Use a real REEF native/headless runtime for them rather than converting them silently.
