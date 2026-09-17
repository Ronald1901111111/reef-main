# Ticket 06 — Cognitive Voice Profiler e Estratificação de Vocabulário

**Fase:** FASE 3 — Voice Model (FLUXO A)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 05  
**Worker Responsável:** Cognitive Voice Profiler (Spark Task)  

---

## Objetivo
Definir os schemas e as diretrizes operacionais do worker Spark responsável por analisar a assinatura textual-discursiva, extrair padrões retóricos com métricas de confiança, selecionar cognitivamente as amostras curadas e estratificar o vocabulário (garantindo que ausência estatística não vire proibição automática).

## Arquivos que Cria ou Modifica
* `schemas/voice_profile.schema.json`
* `schemas/voice_analysis.schema.json`
* `schemas/curated_samples_manifest.schema.json`
* `src/profiler/cognitive_profiler_task.md`
* Template: `projects/voice-rewriter/profiles/ronald_ferrari/profile_overrides.yaml`

## Dependências
* Ticket 05 (`raw_metrics.json`).

## Entradas
* `raw_metrics.json` + transcrições de treino + `profile_overrides.yaml`.

## Saídas
* `voice_analysis.json`, `voice_profile.yaml` e `curated_samples_manifest.json`.

## Critérios de Aceite
- [ ] Estratifica vocabulário em: `characteristic_terms`, `observed_terms`, `rare_terms`, `statistically_unobserved_terms` e `explicitly_forbidden_terms`.
- [ ] `explicitly_forbidden_terms` é preenchido exclusivamente a partir de decisão humana explícita em `profile_overrides.yaml` (ausência estatística nunca vira veto automático). O Profiler pode sugerir termos, mas eles só entram em `explicitly_forbidden_terms` com aprovação humana.
- [ ] Padrões retóricos (hooks, transições, perguntas, CTAs) incluem `confidence` (0.0 a 1.0) e `supporting_transcripts` ($\ge 1$).
- [ ] Seleciona e justifica cognitivamente as amostras para `curated_samples_manifest.json`, classificando por categoria (`hook`, `technical_explanation`, `transition`, `analogy`, `argumentation`, `cta`, `closing`) com justificativa retórica e confiança.
- [ ] O conjunto `calibration/` permanece estritamente inacessível para o Cognitive Voice Profiler.

## Testes Necessários
* `tests/test_cognitive_profiler_contracts.py`:
  * Validar que ausência estatística não é classificada como proibição explícita.
  * Validar conformidade dos schemas de análise e manifesto de amostras curadas.

## Definition of Done
Schemas e prompt operacional do Cognitive Voice Profiler validados e documentados.
