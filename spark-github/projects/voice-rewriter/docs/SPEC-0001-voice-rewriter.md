# SPEC-0001: Motor de Aprendizado de Voz e Reescrita Desestilizada de Roteiros (Voice-Rewriter)

**Documento:** `SPEC-0001` (Revisão 4 — Final Aprovada com Erratas Técnicas 1, 2 e 3)  
**Status:** `APPROVED`  
**Arquitetura Base:** REEF + Gemini Spark (Workers Independentes) + GitHub (Filas, Memória e Triggers) + GitHub Actions (CI Determinístico)  
**Autor:** Ronald Ferrari / Gemini Spark  

---

## 1. Declaração de Propósito e Tese do Produto

O objetivo do subsistema **`voice-rewriter`** não é parafrasear transcrições externas trocando palavras. O produto é:

> **Aprender empiricamente a assinatura textual, estilométrica e retórico-linguística do criador a partir de um corpus validado dos seus próprios vídeos; isolar integralmente essa identidade de qualquer conteúdo externo; e utilizar exclusivamente a representação semântica e causal (outline desestilizado) extraída de uma referência para redigir, do zero, um roteiro inédito na voz do autor.**

$$\text{MEUS VÍDEOS} \longrightarrow \text{CORPUS VALIDADO} \longrightarrow \text{APRENDER MINHA VOZ} \longrightarrow \text{VOICE MODEL BUNDLE}$$
$$\text{OUTRO VÍDEO} \longrightarrow \text{INGESTÃO} \longrightarrow \text{REMOVER ESTILO DA FONTE} \longrightarrow \text{EXTRAIR RACIOCÍNIO} \longrightarrow \text{OUTLINE NEUTRO}$$
$$\text{VOICE MODEL + OUTLINE} \longrightarrow \text{ESCREVER DO ZERO} \longrightarrow \text{CI MECÂNICO} \longrightarrow \text{REVIEW} \longrightarrow \text{EVALUATE} \longrightarrow \text{ITERAÇÃO} \longrightarrow \text{APROVAÇÃO HUMANA} \longrightarrow \text{ROTEIRO FINAL}$$

---

## 2. Erratas Técnicas Incorporadas

1. **Ingestion Core vs. URL Acquisition Adapter:** O núcleo de parsing e normalização de `.txt`, `.srt` e texto manual é 100% determinístico e offline. A aquisição de transcrições via URL é isolada em um adaptador de rede com fallback explícito para `WAITING_FOR_TRANSCRIPT`. O GitHub Actions permanece sem acesso a rede externa ou chaves de IA.
2. **Controle de Concorrência Otimista (OCC) e Leases:** Remoção de falsas alegações de atomicidade no sistema de arquivos Git. O claim de jobs implementa *Optimistic Concurrency Control* via verificação de revisão/SHA do arquivo na fila (`queue_revision`) e política de execução serializada por worker/fila na v1. Contrato inclui `queue_revision`, `claim_status`, `claim_owner`, `claimed_at`, `lease_expires_at`, `attempt` e `idempotency_key`.
3. **Ciclo CI Determinístico Estruturado:** O workflow `voice-pipeline-ci.yml` dispara exclusivamente por push em `candidates/**`, gerando `lint_reports/lint_<job_id>_vX.json`. A máquina de estados formaliza os ciclos `CI_PENDING`, `CI_PASSED` e `CI_FAILED`, roteando para `queues/review/` ou `queues/controller/`.
