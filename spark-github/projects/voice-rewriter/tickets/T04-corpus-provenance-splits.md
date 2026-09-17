# Ticket 04 — Proveniência do Corpus e Isolamento Training/Calibration

**Fase:** FASE 1 — Voice Corpus  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 01  
**Worker Responsável:** Data Prep / Foundation  

---

## Objetivo
Implementar o contrato de metadados de proveniência e o validador de integridade do Voice Corpus, garantindo a pureza autoral do treino e o isolamento físico estrito entre os conjuntos de treino e calibração.

## Arquivos que Cria ou Modifica
* `schemas/transcript_metadata.schema.json`
* `src/corpus/corpus_validator.py`
* Estrutura de pastas:
  * `projects/voice-rewriter/voice_corpus/training/`
  * `projects/voice-rewriter/voice_corpus/calibration/`
  * `projects/voice-rewriter/voice_corpus/metadata/`
  * `projects/voice-rewriter/voice_corpus/calibration_manifests/`

## Dependências
* Ticket 01 (Estrutura de diretórios).

## Entradas
* Transcrições em `.txt` e metadados JSON associados em `metadata/`.

## Saídas
* `src/corpus/corpus_validator.py` e manifesto de calibração gerado `calibration_manifests/calibration_v1.json`.

## Critérios de Aceite
- [ ] Rejeita para treino qualquer transcrição onde `eligible_for_voice_learning` seja `false`, `contains_guests` seja `true` ou `authorship_verified` seja `false`.
- [ ] Garante que nenhum arquivo em `calibration/` apareça ou seja referenciado no conjunto de `training/`.
- [ ] Gera `calibration_manifests/calibration_v1.json` contendo a lista exata e hashes SHA-256 de todos os arquivos de calibração vigentes.

## Testes Necessários
* `tests/test_corpus_integrity.py`:
  * Rejeição de transcrições com convidados ou autoria não verificada.
  * Detecção e bloqueio de data leakage (sobreposição de arquivos entre treino e calibração).
  * Validação de integridade de hashes no manifesto de calibração.

## Definition of Done
Validador executável via linha de comando atestando a conformidade e integridade do corpus.
