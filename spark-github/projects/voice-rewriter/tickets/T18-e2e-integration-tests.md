# Ticket 18 — Testes Integrados E2E A (Voice Learning) e E2E B (Rewriting)

**Fase:** FASE 13 — End-to-End  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 07, Ticket 16, Ticket 17  
**Worker Responsável:** Integration / Controller  

---

## Objetivo
Validar de forma completa e independente os dois fluxos do sistema (Aprendizado de Voz e Reescrita de Vídeo Externo) em suites ponta a ponta desacopladas.

## Arquivos que Cria ou Modifica
* `tests/e2e/test_e2e_voice_learning.py` (E2E A)
* `tests/e2e/test_e2e_rewriting.py` (E2E B)
* Fixtures em `tests/fixtures/e2e/`

## Dependências
* Ticket 07 (Voice Model Bundle), Ticket 16 (Human Approval), Ticket 17 (Runbook e Runtime).

## Entradas
* Transcrições reais de treino e calibração + transcrição externa de teste.

## Saídas
* Relatórios de validação dos testes integrados E2E A e E2E B.

## Critérios de Aceite
- [ ] **E2E A (Voice Learning Flow):** Executa o fluxo completo do corpus de treino, gerando métricas brutas, análise cognitiva com confiança e o bundle imutável versionado. Valida que `calibration/` permaneceu intocado.
- [ ] **E2E B (Rewriting Flow):** Executa Ingestão → Semantic Extraction → Writing → CI determinístico → Review → Evaluation (contra calibração congelada) → Controller → Aprovação formal simulada → Promoção para `outputs/`.
- [ ] O E2E B consome o bundle pré-compilado do E2E A sem reexecutar o profiling de voz.
- [ ] Simulação de interrupção de worker e recuperação de lease sem geração duplicada de candidatos confirmada.

## Testes Necessários
* `tests/e2e/test_e2e_voice_learning.py`
* `tests/e2e/test_e2e_rewriting.py`

## Definition of Done
Ambos os fluxos executam e passam de ponta a ponta com 100% de conformidade aos critérios da especificação.
