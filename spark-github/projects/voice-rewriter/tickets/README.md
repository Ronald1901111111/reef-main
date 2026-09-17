# Índice Geral de Tickets: Voice-Rewriter

**Projeto:** Voice-Rewriter (Subprojeto do REEF)  
**Status Geral:** `IN_PROGRESS` (Tickets 01, 02 e 03 concluídos)  
**Total de Tickets:** 18  

---

## Tabela de Tickets e Dependências

| Ticket | Título | Fase | Worker Responsável | Bloqueado por | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[T01](./T01-foundation-structure-schemas.md)** | Estrutura de Diretórios e Schemas de Estado e Filas | FASE 0 | Foundation | Nenhum | `DONE` |
| **[T02](./T02-queue-manager-worker-runtime.md)** | Queue Manager, Contrato Operacional e Menor Acesso | FASE 0 | Foundation | T01 | `DONE` |
| **[T03](./T03-state-machine-core.md)** | State Machine Core | FASE 0 | Foundation | T01 | `DONE` |
| **[T04](./T04-corpus-provenance-splits.md)** | Proveniência do Corpus e Isolamento Training/Calibration | FASE 1 | Data Prep | T01 | `NOT_STARTED` |
| **[T05](./T05-deterministic-profiler.md)** | Profiler Determinístico de Métricas Estilométricas | FASE 2 | Deterministic Profiler | T04 | `NOT_STARTED` |
| **[T06](./T06-cognitive-voice-profiler.md)** | Cognitive Voice Profiler e Estratificação de Vocabulário | FASE 3 | Cognitive Profiler (Spark) | T05 | `NOT_STARTED` |
| **[T07](./T07-voice-model-bundle-compiler.md)** | Voice Model Bundle Imutável e Compilador de Prompt | FASE 3 | Profiler / Compiler | T06 | `NOT_STARTED` |
| **[T08](./T08-ingestion-core.md)** | Ingestion Core Determinístico (Parsing e Normalização) | FASE 4 | Ingestion Core | T01, T02, T03 | `NOT_STARTED` |
| **[T09](./T09-url-acquisition-adapter.md)** | URL Acquisition Adapter e Fallback de Transcrição | FASE 4 | Ingestion Adapter | T08 | `NOT_STARTED` |
| **[T10](./T10-semantic-extractor.md)** | Semantic Extractor e Schema de De-styling Causal | FASE 5 | Semantic Extractor (Spark) | T08 | `NOT_STARTED` |
| **[T11](./T11-voice-writer.md)** | Voice Writer com Barreira Estrutural de Menor Acesso | FASE 6 | Voice Writer (Spark) | T07, T10 | `NOT_STARTED` |
| **[T12](./T12-voice-linter-ci-router.md)** | Voice Linter Determinístico, CI e Result Router | FASE 7 | Mechanical Runner (Actions) | T01, T03 | `NOT_STARTED` |
| **[T13](./T13-reviewer.md)** | Reviewer de Contaminação Estilística e Fluidez | FASE 8 | Reviewer (Spark) | T10, T11, T12 | `NOT_STARTED` |
| **[T14](./T14-evaluator.md)** | Evaluator de Similaridade com Calibração Congelada | FASE 9 | Evaluator (Spark) | T04, T07, T12, T13 | `NOT_STARTED` |
| **[T15](./T15-controller-circuit-breaker.md)** | Controller de Transições e Circuit Breaker | FASE 10 | Controller (Spark) | T02, T03, T14 | `NOT_STARTED` |
| **[T16](./T16-human-approval-promoter.md)** | Protocolo de Aprovação Humana Formal e Promoter | FASE 11 | Promoter / Controller | T03, T15 | `NOT_STARTED` |
| **[T17](./T17-spark-workers-runbook-provisioning.md)** | Provisionamento e Runbook dos Workers Spark | FASE 12 | Runtime / Infra | T02, T03, T09, T15, T16 | `NOT_STARTED` |
| **[T18](./T18-e2e-integration-tests.md)** | Testes Integrados E2E A (Voice) e E2E B (Rewriting) | FASE 13 | Integration / Controller | T07, T16, T17 | `NOT_STARTED` |

---

## Grafo de Execução

```text
T01 ──┬──> T02 ─────────┬───────────────────────> T08 ──┬──> T09 ──┐
      ├──> T03 ──┬──────┤                        │     └──> T10 ──┼──> T11 ──> T13 ──> T14 ──> T15 ──> T16 ──┬──> T18
      │          │      └────────────────────────┤                 │      ▲      ▲             ▲           │     ▲
      │          ├───────────────────────────────┼──> T12 ─────────┴──────┤      │             │           │     │
      │          └───────────────────────────────┼────────────────────────┼──────┼─────────────┼───────────┤     │
      │                                          └────────────────────────┼──────┼─────────────┴──> T17 ───┘     │
      └──> T04 ──> T05 ──> T06 ──> T07 ───────────────────────────────────┴──────┴─────────────────────────────────┘
```
