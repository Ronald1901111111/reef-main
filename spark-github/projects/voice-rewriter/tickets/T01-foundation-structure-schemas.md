# Ticket 01 — Estrutura de Diretórios e Schemas de Estado e Filas

**Fase:** FASE 0 — Fundação e Governança  
**Status:** `DONE`  
**Bloqueado por:** Nenhum (Pode iniciar imediatamente).  
**Worker Responsável:** Foundation / Controller  

---

## Objetivo
Criar a estrutura base de diretórios no repositório e formalizar os contratos de schema JSON canônicos separando estritamente o **Queue Lifecycle** (vida útil do worker na fila) do **Job Lifecycle** (estado global da reescrita do roteiro), além de suportar referências congeladas de bundle e calibração.

## Arquivos que Cria ou Modifica
* `schemas/job_state.schema.json` (Fonte canônica única)
* `schemas/queue_envelope.schema.json` (Fonte canônica única)
* `tests/test_schemas_foundation.py`
* Pastas com `.gitkeep`:
  * `spark-github/queues/ingestion/.gitkeep`
  * `spark-github/queues/voice_profiling/.gitkeep`
  * `spark-github/queues/semantic_extraction/.gitkeep`
  * `spark-github/queues/writing/.gitkeep`
  * `spark-github/queues/review/.gitkeep`
  * `spark-github/queues/evaluation/.gitkeep`
  * `spark-github/queues/controller/.gitkeep`
  * `spark-github/state/jobs/.gitkeep`

## Dependências
* Nenhuma.

## Entradas
* Definições de atributos e estados da SPEC-0001 (Rev 4).

## Saídas
* Arquivos de schema JSON válidos, testes automatizados e árvores de diretórios comitadas.

## Critérios de Aceite
- [x] `queue_envelope.schema.json` valida estritamente o Queue Lifecycle: `QUEUED`, `CLAIMED`, `RUNNING`, `COMPLETED`, `FAILED`.
- [x] `queue_envelope.schema.json` exige campos de OCC e idempotência: `job_id`, `run_id`, `queue_revision`, `claim_status`, `claim_owner`, `claimed_at`, `lease_expires_at`, `attempt` e `idempotency_key`.
- [x] `job_state.schema.json` formaliza todos os 18 estados do Job Lifecycle: `WAITING_FOR_TRANSCRIPT`, `SEMANTIC_EXTRACTION_PENDING`, `SEMANTIC_EXTRACTION_COMPLETED`, `WRITING_PENDING`, `CANDIDATE_GENERATED`, `CI_PENDING`, `CI_PASSED`, `CI_FAILED`, `REVIEW_PENDING`, `REVIEW_COMPLETED`, `EVALUATION_PENDING`, `EVALUATED`, `ITERATING`, `NEEDS_HUMAN_REVIEW`, `READY_FOR_HUMAN_APPROVAL`, `APPROVED_BY_HUMAN`, `PROMOTED`, `FAILED`.
- [x] O estado `PROMOTED` é o único estado terminal de sucesso global.
- [x] `job_state.schema.json` prevê os campos imutáveis: `voice_model_bundle_path` e `calibration_manifest_path`.
- [x] Unicidade de fonte: os schemas residem exclusivamente na pasta canônica `schemas/`, sem espelhamento duplicado.

## Testes Necessários
* `tests/test_schemas_foundation.py`:
  * Validar envelopes de fila válidos contra o schema.
  * Rejeitar envelopes sem `queue_revision` ou `idempotency_key`.
  * Validar instâncias do estado global do job.
  * Rejeitar estados inválidos ou contaminação entre QueueState e JobState.

## Definition of Done
Todos os schemas canônicos validados com ferramenta de teste de schema JSON (`pytest tests/test_schemas_foundation.py -v`) com 100% de aprovação e diretórios comitados no repositório na branch `feature/voice-rewriter-t01-foundation`.
