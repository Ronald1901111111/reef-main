# Ticket 12 — Voice Linter Determinístico, CI e Result Router

**Fase:** FASE 7 — Deterministic CI (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 01, Ticket 03 (Desenvolvido contra fixtures em `tests/fixtures/candidates/`, desacoplado do Voice Writer)  
**Worker Responsável:** Mechanical Runner (Python / GitHub Actions)  

---

## Objetivo
Implementar o validador mecânico em Python, o workflow do GitHub Actions disparado por push em `candidates/` e o roteador determinístico de resultado que avança o job sem envolver IA, registrando permissões mínimas e protegendo contra loops de execução.

## Arquivos que Cria ou Modifica
* `src/validator/voice_linter.py`
* `src/validator/ci_router.py`
* `schemas/lint_report.schema.json`
* `.github/workflows/voice-pipeline-ci.yml`
* Saída: `spark-github/lint_reports/lint_<job_id>_vX.json`

## Dependências
* Ticket 01, Ticket 03.

## Entradas
* `candidate_<job_id>_vX.md` + bundle versionado (`voice_profile.yaml`).

## Saídas
* `lint_reports/lint_<job_id>_vX.json` e job enfileirado na próxima fila correspondente.

## Critérios de Aceite
- [ ] O workflow do GitHub Actions reage exclusivamente a `projects/voice-rewriter/candidates/**` (nunca a `lint_reports/**`), evitando recursão.
- [ ] Utiliza permissões mínimas no workflow (`contents: write`).
- [ ] Reprova imediatamente se encontrar termos de `explicitly_forbidden_terms` ou frases $> 24$ palavras.
- [ ] Emite apenas warning para `statistically_unobserved_terms` sem falhar o status `PASSED`.
- [ ] Preserva no relatório: `job_id`, `candidate_version` e `voice_model_version`.
- [ ] **CI Result Router:** Se `PASSED`, atualiza o estado para `CI_PASSED` e enfileira em `queues/review/`; se `FAILED`, atualiza para `CI_FAILED` e enfileira em `queues/controller/`.

## Testes Necessários
* `tests/test_voice_linter.py`:
  * Casos de veto determinístico por palavras proibidas e sentenças longas.
  * Casos de aprovação com avisos para vocabulário não observado.
* `tests/test_ci_router.py`:
  * Roteamento determinístico para `review/` quando aprovado e `controller/` quando reprovado.

## Definition of Done
Linter e CI Result Router operacionais e testados com fixtures em ambiente offline.
