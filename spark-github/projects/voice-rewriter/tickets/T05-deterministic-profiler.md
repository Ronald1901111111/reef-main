# Ticket 05 — Profiler Determinístico de Métricas Estilométricas

**Fase:** FASE 2 — Deterministic Profiling  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 04  
**Worker Responsável:** Deterministic Profiler (Python / Actions)  

---

## Objetivo
Implementar o profiler determinístico e offline que calcula métricas estatísticas, sintáticas e léxicas brutas sobre o corpus de treino sem invocar LLMs ou conexões de rede.

## Arquivos que Cria ou Modifica
* `src/profiler/deterministic_profiler.py`
* `schemas/raw_metrics.schema.json`
* `.github/workflows/deterministic-profiler.yml`

## Dependências
* Ticket 04 (Corpus de treino validado).

## Entradas
* Arquivos `.txt` validados de `voice_corpus/training/`.

## Saídas
* `raw_metrics.json` contendo distribuições estatísticas brutas.

## Critérios de Aceite
- [ ] Calcula com precisão matemática: média, desvio padrão, mínimo e máximo de palavras por sentença.
- [ ] Extrai densidade de pontuação, n-grams funcionais e riqueza lexical (MTLD).
- [ ] Sanitiza timestamps residuais sem adulterar as palavras do autor.
- [ ] Workflow do GitHub Actions é configurado para disparar exclusivamente por push em `voice_corpus/training/**` e gerar o relatório como artefato versionado.

## Testes Necessários
* `tests/test_deterministic_profiler.py`:
  * Comparação das métricas geradas contra textos sintéticos com contagens pré-calculadas.
  * Validação de schema do `raw_metrics.json` produzido.

## Definition of Done
Script CLI executável localmente e workflow CI configurado, gerando métricas válidas e reprodutíveis.
