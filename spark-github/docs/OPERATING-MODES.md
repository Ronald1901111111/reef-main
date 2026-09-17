# Operating Modes

## Mode 1 — Spark-driven, no model API (default)

Spark reads/writes the repository through GitHub MCP/tools. Spark creates the candidate. GitHub Actions validates and packages. Spark runs the comparison and records the result. Promotion requires human approval.

Fixed infrastructure cost can be zero, subject to the user's GitHub/Spark plans and GitHub Actions included minutes.

This mode preserves REEF's flat harness-tree vocabulary and versioned candidate/release workflow, but it is not REEF's autonomous proposer/evaluator recipe.

## Mode 2 — Full autonomous REEF (optional later)

A GitHub Action or external runtime starts REEF `harness-evolve`/Reefine with a programmatic model endpoint. REEF can then propose/evaluate candidates without an interactive Spark task.

This mode is not enabled by the starter because it requires server-side model credentials/endpoints and can incur usage costs.

## Why there is no fake `spark` REEF execution adapter

REEF's harness adapters map trees to third-party coding-agent runtimes that can be launched headlessly and produce trajectories. Spark uploads do not expose the same executable CLI contract. The starter therefore uses an exporter/controller boundary instead of registering an adapter that could render files but not honestly execute/evaluate them.
