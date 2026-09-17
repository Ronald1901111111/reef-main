# Ticket 03 — State Machine Core

**Fase:** FASE 0 — Fundação e Governança  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 01  
**Worker Responsável:** Foundation  

---

## Objetivo
Criar o autômato de estados formal que declara, valida e aplica todas as transições legais do Job Lifecycle e do Queue Lifecycle, disponibilizando funções utilitárias reutilizáveis para todos os workers e componentes do sistema.

## Arquivos que Cria ou Modifica
* `src/core/state_machine.py`
* `tests/test_state_machine.py`

## Dependências
* Ticket 01 (Definição dos schemas de estados).

## Entradas
* Estado corrente, estado de destino e contexto de transição.

## Saídas
* Funções: `can_transition(current, target)`, `assert_transition(current, target, context)`, `get_valid_next_states(current)`.

## Critérios de Aceite
- [ ] Isola rigorosamente `QueueState` (`QUEUED`, `CLAIMED`, `RUNNING`, `COMPLETED`, `FAILED`) de `JobState` (18 estados do pipeline).
- [ ] Permite transições legais documentadas (ex: `CI_PENDING` → `CI_PASSED`, `READY_FOR_HUMAN_APPROVAL` → `APPROVED_BY_HUMAN` → `PROMOTED`).
- [ ] Lança `IllegalStateTransitionError` para qualquer salto inválido (ex: `CI_PENDING` → `PROMOTED`, `QUEUED` → `COMPLETED`).
- [ ] Disponibiliza transições para os estados terminais `PROMOTED` e `FAILED`.

## Testes Necessários
* `tests/test_state_machine.py`:
  * Tabela completa de transições válidas testada positivamente.
  * Conjunto exaustivo de transições inválidas rejeitadas com exceção explícita.

## Definition of Done
Módulo de máquina de estados concluído com suite de testes exaustiva e sem dependências externas.
