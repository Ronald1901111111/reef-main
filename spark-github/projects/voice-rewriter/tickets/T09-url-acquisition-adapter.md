# Ticket 09 — URL Acquisition Adapter e Fallback de Transcrição

**Fase:** FASE 4 — Ingestion (FLUXO B)  
**Status:** `DONE`  
**Bloqueado por:** Ticket 08  
**Worker Responsável:** Ingestion Worker (Adapter)  

---

## Objetivo
Implementar o adaptador dependente de rede para capturar legendas automáticas via URL do YouTube, assegurando fallback seguro para `WAITING_FOR_TRANSCRIPT` caso a legenda esteja indisponível.

## Arquivos que Cria ou Modifica
* `src/ingestion/url_adapter.py`
* `src/ingestion/worker.py`

## Dependências
* Ticket 08 (Ingestion Core).

## Entradas
* Job em `queues/ingestion/` com URL do YouTube informada.

## Saídas
* Transcrição bruta baixada e repassada ao Ingestion Core OU job transitado para `WAITING_FOR_TRANSCRIPT`.

## Critérios de Aceite
- [x] Obtém legendas públicas e entrega o texto bruto ao `cleaner.py`.
- [x] Se a URL não possuir legendas públicas ou falhar por bloqueio de rede, transita o estado global do job para `WAITING_FOR_TRANSCRIPT` e suspende o processamento sem quebrar a execução.
- [x] Ao receber a transcrição manual para um job em espera, retoma o fluxo a partir do Ingestion Core.

## Testes Necessários
* `tests/test_url_adapter.py`:
  * Mocks de sucesso de extração de legendas.
  * Mocks de falha de conexão e ausência de legendas atestando a transição para `WAITING_FOR_TRANSCRIPT`.

## Definition of Done
Adaptador de rede isolado operando com tratamento de exceções e fallback de espera confirmado.