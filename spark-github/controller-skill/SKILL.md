---
name: reef-spark-controller
description: Coordinate Spark-driven REEF harness evolution through a connected GitHub repository without requiring a permanent VPS or model API.
---
# REEF Spark Controller

## Mission

Use Gemini Spark as the reasoning layer for a GitHub-hosted REEF-compatible harness workflow. GitHub is the versioned store and GitHub Actions performs deterministic validation, packaging, and explicit promotion.

This skill does **not** claim that the interactive Spark subscription is a programmatic model endpoint for REEF. In the default no-API mode, Spark itself creates and evaluates candidates; Actions does not run an autonomous LLM loop.

Read these support files before changing a harness:

- `GITHUB-PROTOCOL.md`
- `EVALUATION-PROTOCOL.md`
- `REEF-TREE-GUIDE.md`
- `SAFETY-AND-LIMITS.md`

## First-run preflight

Before any mutation:

1. Resolve the exact GitHub repository the user wants to use. If it is not known from the task or connected context, ask for `owner/repository`.
2. Verify these paths exist: `harnesses/`, `candidates/`, `evaluations/`, `tools/`, `.github/workflows/`.
3. Read the target `harnesses/<name>/tree.json` and `evaluations/<name>/cases.json`.
4. Check that the target tree uses only Spark-exportable node kinds unless the user explicitly intends REEF-native evaluation.
5. Report whether GitHub Actions status is actually visible. Never claim CI passed without a visible successful run.

## Default lifecycle

```text
DISCOVER
  -> REQUESTED
  -> CANDIDATE
  -> VALIDATED
  -> EVALUATED
  -> RECOMMENDED
  -> [human approval]
  -> PROMOTED | REJECTED
```

### 1. Record the request

Create:

`requests/<harness>/<request-id>.json`

Use a path-safe id such as `YYYYMMDD-HHMMSS-short-slug`. Preserve the user's request verbatim in a `request` field and include `harness`, `created_by: "gemini-spark"`, and `mode: "no-api"`.

### 2. Create a candidate

Read the current tree and applicable evaluation cases. Produce a complete candidate tree at:

`candidates/<harness>/<candidate-id>/tree.json`

Also write `candidate.json` containing the candidate id, source harness, request id, a concise rationale, and a list of changed entry ids.

Do not modify `harnesses/<name>/tree.json` at this stage.

### 3. Validate/package

Commit the candidate through the connected GitHub tools. A push touching candidate trees triggers `validate-and-package.yml`.

If Actions access is available, inspect the run and require success before calling the candidate `VALIDATED`. If Actions access is unavailable, say `CI STATUS UNKNOWN`; do not substitute local reasoning for CI evidence.

### 4. Evaluate

Follow `EVALUATION-PROTOCOL.md`. Compare the current tree and candidate against the same cases. Record the evaluation under:

`evaluations/<harness>/results/<candidate-id>.json`

A better score produces a **recommendation**, not automatic promotion.

### 5. Ask before promotion

Never write a `PROMOTE` decision or trigger the promotion workflow merely because the candidate scored better. Present the comparison and ask the human whether to promote it.

After explicit approval, set `decision: "PROMOTE"` in the evaluation record and invoke/trigger `promote.yml` if the connected GitHub capability supports Actions. If workflow triggering is unavailable, instruct the user to run `Promote evaluated candidate` in GitHub Actions with the harness and candidate id.

## Rejection

For a rejected candidate, set `decision: "REJECT"`. Keep the candidate and evaluation for history unless the user explicitly asks to delete them.

## Runtime truthfulness

Use only capabilities actually exposed by the connected GitHub integration. Reading a workflow file is not evidence that a workflow ran. Writing a candidate file is not evidence that REEF autonomously generated it. In no-API mode, identify the candidate as Spark-proposed and REEF-compatible.
