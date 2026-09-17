# Ticket 10 — Semantic Extractor e Schema de De-styling Causal

**Fase:** FASE 5 — Semantic Extraction (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 08 (Não depende de T09; testável via fixtures locais)  
**Worker Responsável:** Semantic Extractor (Spark Task)  

---

## Objetivo
Definir o schema e as instruções operacionais do Semantic Extractor para converter a transcrição limpa de terceiros em uma representação semântica e causal neutra (`outline.json`), minimizando ativamente a transferência estilística da origem.

## Arquivos que Cria ou Modifica
* `schemas/outline.schema.json`
* `src/semantic/semantic_extractor_task.md`
* Saída: `outlines/outline_<job_id>.json`

## Dependências
* Ticket 08 (`raw_source.txt`).

## Entradas
* `source_material/<job_id>/raw_source.txt`.

## Saídas
* `outline_<job_id>.json` estruturado e payload sanitizado enfileirado em `queues/writing/`.

## Critérios de Aceite
- [ ] O outline captura obrigatoriamente para cada bloco: `topico`, `afirmacao_ou_tese`, `evidencias_ou_exemplos`, `relacao_causal` e `ressalvas_ou_contrapontos`.
- [ ] Preserva dados numéricos, nomes próprios, fontes e perguntas norteadoras sem carregar os cacoetes do autor original.
- [ ] Constrói o payload para `queues/writing/` aplicando a barreira de menor acesso: inclui apenas `outline_path`, `voice_model_bundle_path`, `job_id` e `iteration` (zero menção a `source_material`).

## Testes Necessários
* `tests/test_outline_schema.py`:
  * Validação de schema do outline causal.
  * Validação de sanitização do payload para a fila de escrita.

## Definition of Done
Schema validado por testes e diretrizes de de-styling estruturadas.
