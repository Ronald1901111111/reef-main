# REEF + GitHub MCP + Gemini Spark Starter

A zero-VPS starter for evolving REEF-compatible text harnesses with Gemini Spark as the reasoning layer and GitHub as storage, CI, packaging, and release history.

## What is included

```text
controller-skill/              Spark skill that drives the workflow
harnesses/<name>/tree.json     current REEF-compatible harness trees
candidates/                    proposed trees, never current by default
evaluations/                   A/B cases and recorded results
releases/                      promoted release history
tools/                         validator, Spark exporter, promotion logic
.github/workflows/             package/validate + explicit promotion
```

## Default flow

```text
Spark
  -> GitHub MCP/tools
  -> read current tree + cases
  -> write request + candidate
  -> push triggers Validate and package
  -> Actions creates Spark ZIP artifacts
  -> Spark evaluates current vs candidate
  -> user approves or rejects
  -> Promote evaluated candidate workflow
  -> current tree + release history updated
```

## First setup

1. Create a GitHub repository and upload this starter repository.
2. Enable GitHub Actions. For the promotion workflow, repository Actions must be permitted to write repository contents.
3. Connect the official GitHub MCP/server or equivalent GitHub connected app to Gemini Spark with access only to this repository when possible.
4. Upload `dist/reef-spark-controller.zip` to Spark as one skill.
5. Start a Spark task with: `Use reef-spark-controller. Repository: OWNER/REPO. Run preflight for harness demo.`

## Packaging

Run locally or in Actions:

```bash
python -m unittest discover -s tests -v
python -m tools.package_repository --repo-root . --out build/spark-bundles
```

For `harnesses/demo/tree.json`, this creates a controller ZIP, one ZIP per Reef `skill`, one ZIP per `agent_command`, and a manifest.

## Important limitation

The default mode does not run REEF's autonomous LLM evolution recipe. Spark is the proposer/evaluator. GitHub Actions performs deterministic operations only. See `docs/OPERATING-MODES.md`.

## Upstream REEF relationship

This project follows the uploaded REEF source's flat harness tree vocabulary and its distinction between portable text nodes and executable/native nodes. It deliberately refuses executable node kinds for Spark export because Spark skill ZIPs do not provide an equivalent headless execution surface.
