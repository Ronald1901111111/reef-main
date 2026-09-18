# Ticket 08 — Ingestion Core Determinístico (Parsing e Normalização Offline)

**Fase:** FASE 4 — Ingestion (FLUXO B)  
**Status:** `DONE`  
**Bloqueado por:** Ticket 01, Ticket 02, Ticket 03  
**Worker Responsável:** Ingestion Worker (Core)  

---

## Objetivo
Implementar o núcleo de ingestão offline e determinístico responsável pelo parsing de arquivos `.txt`, `.srt` e texto manual, higienizando ruídos de estúdio e normalizando o texto sem depender de rede externa.

## Arquivos que Cria ou Modifica
* `src/ingestion/cleaner.py`
* `src/ingestion/parsers.py`
* `src/ingestion/core_cli.py`

## Dependências
* Ticket 01, Ticket 02, Ticket 03.

## Entradas
* Arquivos `.txt`, `.srt` ou string de texto manual de fonte externa.

## Saídas
* `projects/voice-rewriter/source_material/<job_id>/raw_source.txt` normalizado.

## Critérios de Aceite
- [x] Normaliza quebras de linha e remove ruídos textuais de legendas (`[Música]`, `[Aplausos]`, tags de formatação).
- [x] Preserva integralmente números, estatísticas, dados técnicos e nomes próprios.
- [x] Atualiza o estado global do job para `SEMANTIC_EXTRACTION_PENDING` e enfileira em `queues/semantic_extraction/`.

## Testes Necessários
* `tests/test_ingestion_core.py`:\n  * Parsing de arquivos `.srt` reais com timestamps quebrados.
  * Limpeza de ruídos sem perda de vocabulário ou pontuação substantiva.

## Definition of Done
CLI do Ingestion Core operando 100% offline e aprovado em testes unitários.