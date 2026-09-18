# Ticket 13 — Reviewer de Contaminação Estilística e Fluidez

**Fase:** FASE 8 — Review (FLUXO B)  
**Status:** `DONE`  
**Bloqueado por:** Ticket 10, Ticket 11, Ticket 12  
**Worker Responsável:** Reviewer (Spark Task)  

---

## Objetivo
Implementar o worker independente de revisão qualitativa que audita o candidato aprovado no CI, comparando-o com o outline e com o material original para identificar contaminação de estilo, plágio estrutural e avaliar a fluidez para locução.

## Arquivos que Cria ou Modifica
* `src/reviewer/reviewer_task.md`
* Saída: `evaluations/review_<job_id>_vX.md`

## Dependências
* Ticket 10 (`outline.json`), Ticket 11 (`candidate.md`), Ticket 12 (`lint_report.json` com status `PASSED`).

## Entradas
* `candidate_<job_id>_vX.md`, `outline_<job_id>.json`, `source_material/<job_id>/raw_source.txt` e `lint_report.json`.

## Saídas
* Relatório qualitativo de revisão e job enfileirado em `queues/evaluation/` com estado `REVIEW_COMPLETED`.

## Critérios de Aceite
- [x] O Reviewer possui acesso autorizado a `source_material/` exclusivamente para auditoria de plágio e contaminação de frases.
- [x] Detecta calques estruturais e expressões copiadas do autor original.
- [x] Avalia cadência, naturalidade de leitura e preservação dos fatos presentes no outline.
- [x] Enfileira a tarefa na fila `queues/evaluation/`.

## Testes Necessários
* `tests/test_reviewer_contract.py`:
  * Validação do formato do parecer de revisão e das seções obrigatórias de diagnóstico.

## Definition of Done
Instruções operacionais do Reviewer validadas e integração com a fila de avaliação concluída.