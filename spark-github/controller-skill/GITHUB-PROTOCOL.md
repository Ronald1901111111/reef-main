# GitHub Protocol

## Repository layout

```text
harnesses/<harness>/tree.json
requests/<harness>/<request-id>.json
candidates/<harness>/<candidate-id>/tree.json
candidates/<harness>/<candidate-id>/candidate.json
evaluations/<harness>/cases.json
evaluations/<harness>/results/<candidate-id>.json
releases/<harness>/<release-id>/...
```

## Write policy

- Current published state lives only at `harnesses/<harness>/tree.json`.
- Candidate creation never writes to current state.
- Promotion occurs only after explicit human approval and a matching evaluation with `decision: "PROMOTE"`.
- Preserve candidate and evaluation history.
- Do not commit credentials, session cookies, API keys, private transcripts, or unrelated user data.

## Suggested branch policy

When branch creation is available, use `reef/<harness>/<candidate-id>` for candidate work and merge only after validation. If the connected integration cannot create branches, writing candidate paths on the default branch is acceptable because they are inert until promotion.

## Actions

`validate-and-package.yml` is safe to run automatically: it tests and packages but does not promote.

`promote.yml` mutates current state and pushes a commit. Trigger it only after explicit human approval.
