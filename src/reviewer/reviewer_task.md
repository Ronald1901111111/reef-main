# Diretrizes Operacionais do Reviewer (Spark Task)

## Objetivo
Auditar qualitativamente o candidato aprovado no CI contra contaminação estilística da fonte externa e avaliar a fluidez para locução.

## Regras Críticas
1. **Acesso Autorizado a `source_material/`**:
   - Exclusivo para detecção de plágio e contaminação. Não use para reescrever o texto.
2. **Seções Obrigatórias do Parecer**:
   - `Auditoria de Contaminação e Plágio`
   - `Fidelidade Factual ao Outline`
   - `Cadência e Fluidez para Locução`
   - `Veredito Qualitativo`
3. **Enfileiramento**:
   - Ao concluir a auditoria, atualiza o job para `REVIEW_COMPLETED` e enfileira em `queues/evaluation/`.
