# Ticket 14 — Evaluator de Similaridade com Calibração Congelada

**Fase:** FASE 9 — Evaluation (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 04, Ticket 07, Ticket 12, Ticket 13  
**Worker Responsável:** Evaluator (Spark Task)  

---

## Objetivo
Implementar o worker avaliador que afere formalmente a matriz de Voice Similarity, comparando o candidato contra o Voice Profile e contra os roteiros reais do manifesto de calibração congelado no job, aplicando as regras de veto e garantindo reprodutibilidade das avaliações entre iterações.

## Arquivos que Cria ou Modifica
* `schemas/evaluation.schema.json`
* `src/evaluator/evaluator_task.md`
* Saída: `evaluations/eval_<job_id>_vX.json`

## Dependências
* Ticket 04 (Manifesto de calibração), Ticket 07 (Bundle congelado), Ticket 12 (CI report), Ticket 13 (Review report).

## Entradas
* Candidato, `voice_profile.yaml`, referências listadas no `calibration_manifest_path` congelado, `review.md`, `lint_report.json`.

## Saídas
* Relatório de avaliação estruturado e job enfileirado em `queues/controller/` com estado `EVALUATED`.

## Critérios de Aceite
- [ ] Utiliza estritamente os arquivos do `calibration_manifest_path` congelado no job, garantindo que `candidate_v1`, `v2`, `v3` sejam avaliados contra o mesmo baseline idêntico.
- [ ] Pondera maior peso no vocabulário funcional e estilístico (conectores, sintaxe, ritmo), neutralizando o vocabulário temático técnico do assunto.
- [ ] Veto Gates obrigatórios: reprova se `factual_fidelity < 9.5` ou `source_style_contamination > 2.0`.
- [ ] Emite pontuações individuais para as dimensões estilísticas e a decisão recomendada.

## Testes Necessários
* `tests/test_evaluator_schema.py`:
  * Teste de cálculo de pontuação ponderada.
  * Teste de ativação dos portões de veto para factualidade e contaminação.

## Definition of Done
Schema de avaliação validado e matriz de similaridade reproduzível implementada.
