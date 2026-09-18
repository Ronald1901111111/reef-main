# Diretrizes Operacionais do Cognitive Voice Profiler (Spark Task)

## Objetivo
Analisar qualitativamente o corpus de treino para produzir a assinatura retórico-discursiva, o manifesto de amostras curadas e o voice profile com estratificação vocabular.

## Regras Críticas
1. **Estratificação de Vocabulário**:
   - `statistically_unobserved_terms` jamais pode ser tratado como proibição.
   - `explicitly_forbidden_terms` é derivado exclusivamente de aprovação humana explícita em `profile_overrides.yaml`.
2. **Isolamento de Dados**:
   - Nunca leia ou utilize arquivos de `voice_corpus/calibration/`.
3. **Métricas com Confiança**:
   - Padrões discursivos e amostras devem ter nível de confiança (0.0 a 1.0) e transcrições de suporte identificadas.
