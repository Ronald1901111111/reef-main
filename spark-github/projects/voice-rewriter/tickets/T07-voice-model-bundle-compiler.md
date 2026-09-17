# Ticket 07 — Voice Model Bundle Imutável e Compilador de Prompt

**Fase:** FASE 3 — Voice Model (FLUXO A)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 06  
**Worker Responsável:** Profiler / Compiler  

---

## Objetivo
Implementar o compilador determinístico que consome a seleção cognitiva do Ticket 06, valida o manifesto de amostras, compila o `voice_prompt.md` e empacota o Voice Model Bundle como um diretório versionado e imutável protegido por hashes.

## Arquivos que Cria ou Modifica
* `src/profiler/bundle_compiler.py`
* `schemas/bundle_manifest.schema.json`
* Estrutura de saída: `projects/voice-rewriter/profiles/ronald_ferrari/versions/<semver>/`

## Dependências
* Ticket 06 (`voice_profile.yaml`, `curated_samples_manifest.json`, `voice_analysis.json`).

## Entradas
* Artefatos gerados pelo Ticket 06 + transcrições de treino.

## Saídas
* Bundle imutável versionado (ex: `versions/v2.0.0/`) contendo: `raw_metrics.json`, `voice_analysis.json`, `voice_profile.yaml`, `voice_prompt.md`, `curated_samples/` e `bundle_manifest.json`.

## Critérios de Aceite
- [ ] `bundle_manifest.json` calcula hashes SHA-256 de todos os artefatos internos (`profile_hash`, `analysis_hash`, `prompt_hash`, `samples_manifest_hash`, `raw_metrics_hash`).
- [ ] O compilador recusa terminantemente sobrescrever uma versão existente em `versions/<semver>/`, exigindo novo incremento SemVer.
- [ ] O compilador não toma decisões estilísticas: apenas empacota os trechos autorizados pelo manifest e compila deterministicamente o prompt.
- [ ] Nenhuma amostra em `curated_samples/` tem proveniência fora do conjunto de treino.

## Testes Necessários
* `tests/test_bundle_compiler.py`:
  * Teste de recusa de sobrescrita de versão existente.
  * Teste de correspondência exata dos hashes de integridade do manifesto.
  * Teste de compilação determinística do `voice_prompt.md`.

## Definition of Done
Compilador funcional gerando bundles versionados com validação criptográfica de integridade.
