# Quick Start

## 1. Put the starter on GitHub

Create a repository and upload the contents of `reef-spark-github-starter.zip` to its root. Enable GitHub Actions. If you want automated promotion commits, allow Actions to write repository contents.

## 2. Install the Spark controller

Upload `reef-spark-controller.zip` to Gemini Spark as one skill named `reef-spark-controller`.

## 3. Connect Spark to the repository

Connect GitHub through the official GitHub MCP/server or the GitHub connection available in Spark. Prefer repository-scoped access.

## 4. First Spark test

Use:

```text
Use reef-spark-controller.
Repository: OWNER/REPOSITORY.
Run the preflight for harness demo.
Do not modify anything yet. Confirm that you can read:
- harnesses/demo/tree.json
- evaluations/demo/cases.json
- .github/workflows/validate-and-package.yml
Then report the current lifecycle state and which GitHub capabilities you can actually use.
```

Expected behavior: Spark reads the files, identifies the demo harness, and does not create a candidate until asked.

## 5. First candidate

After preflight passes:

```text
Create a candidate for demo that improves how uncertainty is handled. Record the request and candidate in the repository, but do not promote it. Wait for GitHub validation and then show me the A/B evaluation plan.
```

The controller should write under `requests/` and `candidates/`, never directly overwrite `harnesses/demo/tree.json`.

## 6. Promotion

After evaluation, the controller must ask before promotion. Only after explicit approval should the evaluation decision become `PROMOTE` and the promotion workflow run.
