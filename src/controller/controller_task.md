# Diretrizes Operacionais do Controller e Circuit Breaker (Spark Task)

## Objetivo
Gerenciar a orquestração do ciclo de refinamento do candidato, garantindo a integridade dos caminhos congelados e a interrupção segura por Circuit Breaker.

## Regras de Circuit Breaker
1. **Limites Rígidos de Interrupção**:
   - Se `iteration >= 5` ou `failure_count >= 3`:
     Transita obrigatoriamente para `NEEDS_HUMAN_REVIEW` com stage `human_approval`.
2. **Aprovação Automática**:
   - Se `recommendation == "PROCEED_TO_HUMAN_APPROVAL"`:
     Transita para `READY_FOR_HUMAN_APPROVAL` com stage `human_approval`.
3. **Iteração Controlada**:
   - Se reiteração autorizada e limites não atingidos:
     Transita para `ITERATING`, depois `WRITING_PENDING`, incrementa `iteration` e reenfileira em `queues/writing/`.
4. **Imutabilidade**:
   - Preserva `voice_model_bundle_path` e `calibration_manifest_path` sem qualquer alteração.
