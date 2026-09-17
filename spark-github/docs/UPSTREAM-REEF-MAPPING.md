# Upstream REEF Mapping

This integration was designed from the uploaded `Human-Agent-Society/reef` source tree.

The upstream repository defines REEF harness state as a flat Entry tree. Its shared renderer recognizes portable text/config node kinds (`config`, `rules`, `agent_command`, `skill`, `code_extension`) and REEF-native executable kinds (`native_tool`, `native_hook`, `native_graph`, `native_agent`, `native_loop`).

Upstream harness adapters are execution adapters: they map a tree to files expected by a concrete headless runtime such as Codex, Claude, Pi, OpenCode, Hermes, DSH, REEF Native, or Terminus, and the episode system expects a binary plus trajectory contract.

For Gemini Spark this project intentionally does something different:

- `reef-spark-controller` is a Spark skill that coordinates GitHub state and human approval.
- `tools/package_spark.py` is an exporter, not a fake REEF execution adapter.
- `rules`, `skill`, and `agent_command` have meaningful Spark translations.
- `config` is retained as source information only because model/runtime settings belong to Spark.
- executable/native node kinds are rejected for Spark export.

This boundary can later coexist with upstream REEF's autonomous harness recipes when a programmatic model endpoint is available. The default zero-API mode does not replace or mislabel those recipes.
