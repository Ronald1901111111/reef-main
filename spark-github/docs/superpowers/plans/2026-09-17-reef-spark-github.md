# REEF Spark GitHub Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-hosted, Spark-driven REEF harness workflow that validates Reef trees, exports installable Spark skill bundles, records candidate evaluations, and promotes accepted candidates without a permanent VPS or required model API.

**Architecture:** Spark is the reasoning layer and talks to GitHub through MCP. GitHub is the versioned store; GitHub Actions runs deterministic Python tooling. A strict exporter translates REEF `rules`, `skill`, and `agent_command` entries to Spark ZIPs and refuses executable Reef node kinds that Spark cannot faithfully host.

**Tech Stack:** Python 3.12 standard library, JSON state records, GitHub Actions, REEF tree JSON vocabulary, Gemini Spark skill ZIP format.

**Spec:** `docs/superpowers/specs/2026-09-17-reef-spark-github-design.md`

## Global Constraints

- No required VPS.
- No required Gemini/model API in default mode.
- Do not claim Spark can execute Reef code/native node kinds.
- `SKILL.md` must be at ZIP root for every exported Spark skill.
- Candidate changes never overwrite the published harness until promotion.
- Keep credentials out of repository content and Actions logs.

---

### Task 1: Reef tree validator

**Files:**
- Create: `tools/reef_tree.py`
- Create: `tests/test_reef_tree.py`

**Interfaces:**
- Consumes: Reef-compatible `tree.json` arrays.
- Produces: `load_tree(path) -> list[Entry]`, validation errors, supported/unsupported kind classification.

- [ ] Write tests for valid entries, duplicate ids, malformed config, and unsupported Spark node kinds.
- [ ] Run focused tests and verify failure before implementation.
- [ ] Implement typed entry loading and validation.
- [ ] Run focused tests and verify pass.

### Task 2: Spark bundle exporter

**Files:**
- Create: `tools/package_spark.py`
- Create: `tests/test_package_spark.py`

**Interfaces:**
- Consumes: validated Reef tree plus harness name.
- Produces: controller ZIP, component skill ZIPs, command ZIPs, and `manifest.json`.

- [ ] Write tests asserting ZIP root layout, rule inclusion, skill preservation, command policy text, config manifest preservation, and strict refusal of executable nodes.
- [ ] Run focused tests and verify failure.
- [ ] Implement exporter with deterministic ZIP output names and no network dependencies.
- [ ] Run focused tests and verify pass.

### Task 3: Candidate/evaluation/promotion tools

**Files:**
- Create: `tools/check_evaluation.py`
- Create: `tools/promote_candidate.py`
- Create: `tests/test_promotion.py`

**Interfaces:**
- Consumes: candidate tree, evaluation JSON, current harness path.
- Produces: promoted current tree plus archived release copy only when verdict is `PROMOTE`.

- [ ] Write tests for reject/no-op, malformed evaluation, successful promotion, and release archival.
- [ ] Run tests and verify failure.
- [ ] Implement evaluation parsing and promotion.
- [ ] Run tests and verify pass.

### Task 4: GitHub Actions workflows

**Files:**
- Create: `.github/workflows/validate-and-package.yml`
- Create: `.github/workflows/promote.yml`

**Interfaces:**
- Consumes: repository tree/candidate paths.
- Produces: test results, Spark bundle artifacts, and promotion commit on explicit approved evaluation.

- [ ] Add validation/package workflow with Python 3.12, unit tests, exporter invocation, and artifact upload.
- [ ] Add manual promotion workflow with repository write permission, evaluation check, promotion script, tests, and commit.
- [ ] Validate workflow YAML structure locally.

### Task 5: Spark controller skill

**Files:**
- Create: `controller-skill/SKILL.md`
- Create: `controller-skill/GITHUB-PROTOCOL.md`
- Create: `controller-skill/EVALUATION-PROTOCOL.md`
- Create: `controller-skill/REEF-TREE-GUIDE.md`
- Create: `controller-skill/SAFETY-AND-LIMITS.md`

**Interfaces:**
- Consumes: connected GitHub MCP access, repository path, user improvement request.
- Produces: versioned requests/candidates/evaluations and instructions for promotion.

- [ ] Define exact Spark-driven lifecycle and state transitions.
- [ ] Define GitHub file paths and candidate id conventions.
- [ ] Define benchmark comparison and no-API limitation truthfully.
- [ ] Package controller skill ZIP and verify `SKILL.md` at root.

### Task 6: Seed example and documentation

**Files:**
- Create: `harnesses/demo/tree.json`
- Create: `evaluations/demo/cases.json`
- Create: `README.md`
- Create: `docs/OPERATING-MODES.md`

**Interfaces:**
- Demonstrates one complete current-tree -> candidate -> package -> evaluate -> promote flow.

- [ ] Add a safe, text-only demo Reef tree.
- [ ] Add deterministic evaluation cases that Spark can use.
- [ ] Document first-time GitHub/Spark setup and no-API mode.
- [ ] Document optional autonomous REEF mode separately without enabling it.

### Task 7: Verification and distribution

**Files:**
- Create: `dist/reef-spark-controller.zip`
- Create: `dist/reef-spark-github-starter.zip`

**Interfaces:**
- Produces user-uploadable Spark controller and complete GitHub starter repository archive.

- [ ] Run all unit tests.
- [ ] Run demo export and inspect ZIP members.
- [ ] Validate GitHub workflow YAML files parse.
- [ ] Verify no credential-shaped strings or private tokens exist in distributable files.
- [ ] Build both distribution ZIPs.
