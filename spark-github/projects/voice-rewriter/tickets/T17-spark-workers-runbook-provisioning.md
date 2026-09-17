# Ticket 17 — Provisionamento e Runbook dos Workers Spark

**Fase:** FASE 12 — Runtime  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 02, Ticket 03, Ticket 09, Ticket 15, Ticket 16  
**Worker Responsável:** Runtime & Infrastructure  

---

## Objetivo
Documentar a configuração operacional de cada um dos workers como Tasks/Schedules independentes no Gemini Spark, registrando seus contratos de runtime, filas monitoradas, permissões e testes de fumaça, incluindo explicitamente o Ingestion Worker com suporte a URL.

## Arquivos que Cria ou Modifica
* `docs/SPARK_WORKERS_RUNBOOK.md`
* `tests/smoke/test_workers_smoke.py`

## Dependências
* Ticket 02 (Runtime e filas), Ticket 03 (State machine), Ticket 09 (URL adapter e Ingestion), Ticket 15 (Controller), Ticket 16 (Promoter).

## Entradas
* Instruções operacionais desenvolvidas nas Fases 0 a 11.

## Saídas
* `docs/SPARK_WORKERS_RUNBOOK.md` com manual completo de operação e suite de testes de fumaça.

## Critérios de Aceite
- [ ] Documenta para cada um dos 7 workers:
  1. Skill e instruções carregadas.
  2. Queue que monitora no repositório.
  3. Arquivos autorizados para leitura e escrita.
  4. Frequência / Gatilho de schedule no Spark.
  5. Condição de encerramento imediato.
  6. Política de lease e timeout.
  7. Comportamento com fila vazia (encerra limpo com código 0).
- [ ] Registra explicitamente configurações manuais necessárias na interface do Spark.
- [ ] Testes de fumaça verificam que todos os workers acordam, constatam fila vazia e encerram com sucesso.

## Testes Necessários
* `tests/smoke/test_workers_smoke.py`:
  * Execução sequencial de cada worker sobre fila vazia.

## Definition of Done
Runbook operacional completo e testes de fumaça validados.
