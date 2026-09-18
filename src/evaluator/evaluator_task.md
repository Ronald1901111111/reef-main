# Diretrizes Operacionais do Evaluator (Spark Task)

## Objetivo
Avaliar metricamente a similaridade de voz do candidato contra o manifesto de calibração congelado no job, aplicando os portões de veto mandatórios.

## Regras de Veto Mandatórias
1. **Fidelidade Factual**:
   - Se `factual_fidelity < 9.5`: Veto imediato (`factual_fidelity_passed = False`, recomendação `REJECTED` ou `NEEDS_ITERATION`).
2. **Contaminação de Estilo da Fonte**:
   - Se `source_style_contamination > 2.0`: Veto imediato (`contamination_passed = False`, recomendação `NEEDS_ITERATION` ou `REJECTED`).
3. **Calibração Congelada**:
   - Sempre utilize o `calibration_manifest_path` registrado no job inicial. Nunca altere o baseline entre iterações do mesmo job.
