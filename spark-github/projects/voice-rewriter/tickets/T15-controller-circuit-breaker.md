# Ticket 15 — Controller de Transições e Circuit Breaker

**Fase:** FASE 10 — Controller (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 02, Ticket 03, Ticket 14  
**Worker Responsável:** Controller (Spark Task)  

---

## Objetivo
Implementar o worker de controle que interpreta os relatórios de avaliação e linter, gerenciando as iterações de escrita, a preservação dos caminhos congelados do bundle e calibração, a interrupção segura por Circuit Breaker ou o avanço para aprovação humana.

## Arquivos que Cria ou Modifica
* `src/controller/controller_task.md`
* `src/controller/circuit_breaker.py`
* `state/jobs/job_<job_id>.json`

## Dependências
* Ticket 02 (Queue manager), Ticket 03 (State machine), Ticket 14 (`eval.json`).

## Entradas
* `eval_<job_id>_vX.json`, `lint_report.json` e `job_<job_id>.json`.

## Saídas
* Transição de estado para `ITERATING` (com enfileiramento em `writing/`), `READY_FOR_HUMAN_APPROVAL` ou `NEEDS_HUMAN_REVIEW`.

## Critérios de Aceite
- [ ] Circuit Breaker estrito: se `iteration >= 5` ou `failure_count >= 3`, transita obrigatoriamente para `NEEDS_HUMAN_REVIEW` e suspende o avanço automático.
- [ ] Se aprovado na avaliação ($\ge 8.5$ sem vetos), transita para `READY_FOR_HUMAN_APPROVAL`.
- [ ] Em caso de re-iteração, anexa as instruções do Evaluator ao payload do Voice Writer incrementando `iteration`.
- [ ] Garante que `voice_model_bundle_path` e `calibration_manifest_path` permanecem imutáveis em todas as iterações do job.

## Testes Necessários
* `tests/test_controller_circuit_breaker.py`:
  * Interrupção quando `iteration >= 5` ou `failure_count >= 3`.
  * Transição correta para aprovação humana quando o score satisfaz os critérios.

## Definition of Done
Lógica de controle testada contra cenários de aprovação, iteração e parada de emergência.
