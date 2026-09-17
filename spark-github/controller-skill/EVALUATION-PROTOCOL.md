# Evaluation Protocol

## Purpose

Compare the current harness and a candidate on the same cases. Do not evaluate only the candidate.

## Evaluation modes

From strongest to weakest:

1. `installed-a-b`: current and candidate are actually installed/run as separate Spark skills and outputs are compared.
2. `in-context-a-b`: Spark applies the two instruction sets separately in the current task and compares outputs. Useful for iteration, but not identical to installed runtime behavior.
3. `static`: only structural/instruction checks are performed. This cannot prove behavioral improvement.

Record the actual mode in the result.

## Case format

`evaluations/<harness>/cases.json` contains:

```json
{
  "format": "reef-spark-cases-v1",
  "cases": [
    {
      "id": "case-id",
      "prompt": "Task sent to both versions",
      "criteria": ["Observable criterion 1", "Observable criterion 2"]
    }
  ]
}
```

## Result format

```json
{
  "format": "reef-spark-evaluation-v1",
  "harness": "demo",
  "candidate_id": "...",
  "decision": "REJECT",
  "evaluated_by": "gemini-spark",
  "evaluation_mode": "in-context-a-b",
  "cases_total": 3,
  "current_passed": 2,
  "candidate_passed": 3,
  "case_results": [],
  "notes": "..."
}
```

Use `REJECT` while evaluation is pending or until the human explicitly approves promotion. A score advantage alone is not authorization to change it to `PROMOTE`.

## Fair comparison

Keep the prompt, supplied files, context, and acceptance criteria the same between current and candidate. Record any case where the comparison could not be run. Do not count an unrun case as a pass.
