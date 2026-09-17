# REEF + GitHub MCP + Gemini Spark Design

## Goal

Run a zero-fixed-cost, Spark-driven REEF harness workflow without a permanent VPS or Gemini API. Gemini Spark supplies the model reasoning; GitHub stores/version-controls the harness; GitHub Actions performs deterministic validation and packaging; REEF remains the harness data model and optional autonomous backend when a programmatic model endpoint is later added.

## Source constraints from REEF

REEF's harness tree is a flat list of entries. Core portable node kinds include `rules`, `skill`, `agent_command`, `config`, and code/native node kinds. REEF's official adapter abstraction is designed for executable/headless agent runtimes. Gemini Spark does not expose that same CLI execution contract, so this project does not pretend Spark is a normal REEF execution adapter.

The supported Spark export surface in v1 is:

- `rules`: folded into a controller skill.
- `skill`: exported as one independently installable Spark skill ZIP.
- `agent_command`: exported as one independently installable, human-invoked Spark skill ZIP; the policy is instructional because Spark may not enforce the same invocation metadata as Claude/Codex.
- `config`: preserved in the bundle manifest as source information, but not claimed to affect Spark runtime behavior.
- `code_extension`, `native_tool`, `native_hook`, `native_graph`, `native_agent`, `native_loop`: refused by the Spark exporter in v1 because Spark skill uploads do not provide an equivalent execution surface.

## Architecture

```text
Gemini Spark
  |
  | GitHub MCP
  v
GitHub repository
  |- harnesses/<name>/tree.json       current published Reef tree
  |- requests/                         natural-language evolution requests
  |- candidates/                       Spark-proposed Reef trees
  |- evaluations/                      benchmark definitions + Spark verdicts
  |- releases/                         promoted trees + metadata
  |- tools/                            validation/export code
  `- .github/workflows/                deterministic CI/package/promotion
          |
          v
     GitHub Actions
          |
          v
     Spark install bundle artifacts
```

## No-API mode

In the default mode there is no external model API in GitHub Actions. Spark performs the model-dependent operations:

1. Read the current tree and evaluation cases through GitHub MCP.
2. Turn the user's improvement request into a candidate Reef tree.
3. Commit the candidate.
4. GitHub Actions validates the tree and exports installable Spark ZIPs.
5. Spark evaluates current vs candidate using the repository's cases and records the result.
6. If the user approves promotion, Spark writes a `PROMOTE` evaluation record and triggers/requests promotion.

This is Spark-driven harness evolution using REEF's tree vocabulary and versioning pattern. It is not the fully autonomous REEF `harness-evolve` loop because GitHub Actions has no access to the user's interactive Spark subscription as a model endpoint.

## Optional autonomous mode

Later, a programmatic model endpoint can be configured as GitHub secrets and a separate workflow can run REEF's own harness-evolution recipes. This is outside the zero-API v1 and must never be enabled silently.

## Packaging model

A single Reef tree may contain many skills. Spark expects uploaded skills, so the exporter creates a bundle directory:

```text
<name>-spark-bundle/
|- manifest.json
|- controller/<name>-controller.zip
|- skills/<skill-name>.zip
`- commands/<command-name>.zip
```

The controller ZIP contains the rendered `rules` plus a registry of component skills and commands. Each Reef `skill` becomes an independent ZIP with `SKILL.md` at its root. Each `agent_command` becomes an independent ZIP with a human-invoked directive in its `SKILL.md`.

## Repository state

`harnesses/<name>/tree.json` is the current release source. Candidates never overwrite it directly. A candidate lives under `candidates/<name>/<candidate-id>/tree.json` with `candidate.json`. Evaluation results live under `evaluations/<name>/results/<candidate-id>.json`. Promotion copies the accepted candidate into the current harness and archives the previous tree under `releases/<name>/<release-id>/`.

## Security and cost

- No credentials are committed.
- Default workflows need no model secret.
- GitHub Actions is used only for validation, tests, packaging, and promotion.
- No permanent VPS is required.
- No Gemini API is required in default mode.
- Code/native Reef nodes are blocked from Spark export rather than executed on GitHub runners.
