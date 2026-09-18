# Diretrizes Operacionais do Voice Writer (Spark Task)

## Objetivo
Escrever do zero o roteiro candidato utilizando exclusivamente o `outline.json` desestilizado e as diretrizes do `Voice Model Bundle` congelado.

## Regras Críticas de Menor Acesso
1. **Cegueira Estrutural Absoluta**:
   - É terminantemente proibido ler ou acessar `source_material/`. Se qualquer menção ao material de origem for detectada, aborte imediatamente.
2. **Blocos Obrigatórios de Produção**:
   - Hook / Abertura direta
   - Desenvolvimento com relações causais explícitas
   - Transições assertivas
   - Chamada para Ação (CTA) / Fechamento
3. **Anotações de Cadência e Visuais**:
   - Inserir marcações de ritmo como `[PAUSA]` e `[ÊNFASE]`.
   - Incluir notas de tela/visuais sucintas para guiar o apresentador.
4. **Preservação de Referências Congeladas**:
   - Não altere `voice_model_bundle_path` ou `calibration_manifest_path` no job state.
