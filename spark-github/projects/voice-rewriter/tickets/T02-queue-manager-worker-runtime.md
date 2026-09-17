# Ticket 02 — Queue Manager, Contrato Operacional dos Workers e Barreira de Menor Acesso

**Fase:** FASE 0 — Fundação e Governança  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 01  
**Worker Responsável:** Foundation  

---

## Objetivo
Implementar a biblioteca em Python que gerencia operações nas filas com controle de concorrência otimista (OCC), leases de claim, sanitização de payloads de menor acesso e o ciclo operacional padrão de execução dos workers Spark.

## Arquivos que Cria ou Modifica
* `src/core/queue_manager.py`
* `src/core/worker_runtime.py`
* `src/core/exceptions.py`

## Dependências
* Ticket 01 (Schemas de envelope e estado).

## Entradas
* Caminho de fila, `job_id`, dados de identificação do worker e payload.

## Saídas
* Métodos: `enqueue_job()`, `claim_job()`, `complete_queue_item()`, `fail_queue_item()`, `run_worker_cycle()`.

## Critérios de Aceite
- [ ] `claim_job()` verifica `queue_revision`; se o arquivo sofreu alteração concorrente, rejeita com `OptimisticLockError`.
- [ ] Permite recuperação de lease vencido (`current_time > lease_expires_at`), transferindo a posse para a nova execução.
- [ ] Sanitiza o payload da fila `writing/`: remove obrigatoriamente qualquer menção a `source_path`, `raw_source` ou URLs de origem.
- [ ] Implementa o ciclo operacional padrão em `worker_runtime.py`: Wake → Poll Queue → Claim → Load Authorized Inputs → Mark Running → Execute One Stage → Persist Output → Update Global State → Enqueue Next Stage → Complete Queue Item → Exit.
- [ ] Nenhuma execução entra em loop infinito: processa exatamente 1 job e encerra.

## Testes Necessários
* `tests/test_queue_manager.py`:
  * Teste de disputa concorrente por OCC.
  * Teste de expiração e retração de lease.
  * Teste de sanitização estrutural da barreira de menor acesso no payload de writing.
  * Teste de execução de ciclo único com saída limpa.

## Definition of Done
Biblioteca testada com 100% de sucesso nas asserções de concorrência, lease e sanitização de dados.
