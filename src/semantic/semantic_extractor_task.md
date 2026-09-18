# Diretrizes do Semantic Extractor (Spark Task)

## Objetivo
Converter o material bruto higienizado (`source_material/<job_id>/raw_source.txt`) em um `outline.json` causal e desprovido dos vícios de linguagem e estilo do autor original.

## Regras Críticas
1. **Estrutura de Blocos Obrigatória**:
   Cada bloco deve cobrir:
   - `topico`
   - `afirmacao_ou_tese`
   - `evidencias_ou_exemplos` (nomes próprios, números e estatísticas preservados)
   - `relacao_causal`
   - `ressalvas_ou_contrapontos`
2. **De-styling Causal**:
   - Elimine bordões, piadas internas e cadência do orador original.
   - Isole puramente a cadeia lógica de causa e efeito.
3. **Barreira de Menor Acesso para Escrita**:
   - O Voice Writer nunca acessa o texto bruto da fonte, apenas o outline gerado e o Voice Model Bundle.
