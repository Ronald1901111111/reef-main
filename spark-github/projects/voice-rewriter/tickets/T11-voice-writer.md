# Ticket 11 — Voice Writer com Barreira Estrutural de Menor Acesso

**Fase:** FASE 6 — Writing (FLUXO B)  
**Status:** `NOT_STARTED`  
**Bloqueado por:** Ticket 07, Ticket 10  
**Worker Responsável:** Voice Writer (Spark Task)  

---

## Objetivo
Implementar o worker de escrita que consome exclusivamente o outline semântico e o Voice Model Bundle congelado no job para produzir o roteiro novo do zero em Blocos de Produção, mantendo estrita cegueira em relação à transcrição externa.

## Arquivos que Cria ou Modifica
* `src/writer/voice_writer_task.md`
* Saída: `candidates/candidate_<job_id>_vX.md`

## Dependências
* Ticket 07 (Voice Model Bundle congelado), Ticket 10 (Outline semântico).

## Entradas
* Payload sanitizado de `queues/writing/` contendo `outline_path` e `voice_model_bundle_path`.

## Saídas
* Roteiro candidato `candidate_<job_id>_vX.md` e estado global atualizado para `CI_PENDING`.

## Critérios de Aceite
- [ ] O worker rejeita a execução se receber qualquer referência ou caminho a `source_material/`.
- [ ] Estrutura o roteiro em Blocos de Produção (Hook, Desenvolvimento, Transições, CTA) com anotações de cadência (`[PAUSA]`, `[ÊNFASE]`) e notas visuais concisas.
- [ ] Persiste o candidato versionado no repositório (`_v1.md`, `_v2.md`).
- [ ] Mantém congelados os caminhos do bundle e do manifesto de calibração no estado global do job.

## Testes Necessários
* `tests/test_voice_writer_security.py`:
  * Bloqueio por violação da barreira de menor acesso.
  * Validação da presença dos blocos obrigatórios de produção no candidato gerado.

## Definition of Done
Instruções operacionais validadas e candidato gerado com isolamento estrutural comprovado.
