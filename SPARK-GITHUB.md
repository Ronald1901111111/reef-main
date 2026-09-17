# Gemini Spark + GitHub integration

The REEF source in this repository is unchanged. The Spark/GitHub integration lives under `spark-github/`.

Start with `spark-github/QUICKSTART.md`. Upload `spark-github/dist/reef-spark-controller.zip` to Gemini Spark, connect Spark to this repository through GitHub MCP/tools, and run the preflight against `spark-github/harnesses/demo/tree.json`.

The default integration is no-API: Spark proposes/evaluates candidates, while GitHub Actions validates, packages, and explicitly promotes them. Full autonomous REEF recipes remain available in the upstream source but require a programmatic model endpoint.

## Actions-cost safeguard

This fork-ready package moves the upstream REEF GitHub workflows out of `.github/workflows/` and into `.github/upstream-workflows-disabled/` with `.disabled` suffixes. This prevents a first push from unexpectedly running the upstream CI/release matrix and consuming Actions minutes. The REEF source code is otherwise left intact. Restore any upstream workflow deliberately if you need it.
