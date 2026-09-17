# Ticket 16 — Protocolo de Aprovação Humana Formal e Promoter

**Fase:** FASE 11 — Approval (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 03, Ticket 15  
**Worker Responsável:** Promoter / Controller  

---

## Objetivo
Implementar a trava formal de governança que exige um artefato explícito assinado pelo Ronald para promover o roteiro final para a pasta de outputs, finalizando o job com estado `PROMOTED`.

## Arquivos que Cria ou Modifica
* `schemas/approval.schema.json`
* `src/controller/promoter.py`
* `spark-github/approvals/approval_<job_id>_vX.json`
* Saída: `projects/voice-rewriter/outputs/<slug_video_aprovado>.md`

## Dependências
* Ticket 03 (State machine), Ticket 15 (Job em `READY_FOR_HUMAN_APPROVAL`).

## Entradas
* Job em `READY_FOR_HUMAN_APPROVAL` + arquivo `approval_<job_id>_vX.json` assinado.

## Saídas
* Roteiro promovido em `outputs/` e estado global atualizado para `PROMOTED`.

## Critérios de Aceite
- [ ] Bloqueia qualquer tentativa de cópia para `outputs/` se o arquivo de aprovação formal não existir ou divergir de `job_id` / `candidate_version`.
- [ ] O queue item do Promoter transita para `COMPLETED`, enquanto o estado global do job transita estritamente para `PROMOTED` (estado terminal definitivo de sucesso).
- [ ] Nenhuma promoção automática ocorre sem o artefato formal de aprovação.

## Testes Necessários
* `tests/test_promoter.py`:
  * Bloqueio por ausência de aprovação.
  * Promoção bem-sucedida e transição de estado quando a aprovação formal existe.

## Definition of Done
Trava de aprovação humana operando com artefatos persistidos e testada deterministicamente.
