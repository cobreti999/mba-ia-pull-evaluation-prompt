# Revisão manual — requisito 5

Os seis testes exigidos foram implementados em [tests/test_prompts.py](../tests/test_prompts.py).
Eles validam diretamente o [prompt v2 entregue](../prompts/bug_to_user_story_v2.yml),
sem chamadas à OpenAI ou ao LangSmith.

## O que revisar e por quê

| Trecho | Comportamento | Motivo |
| --- | --- | --- |
| Fixture `prompt` | Carrega o YAML por caminho absoluto derivado do arquivo de teste e seleciona a chave v2. | Validar o artefato entregue sem depender do diretório corrente. |
| `test_prompt_has_system_prompt` | Exige string não vazia, rejeitando campo ausente ou tipo incorreto. | Evitar um prompt sem instruções de sistema. |
| `test_prompt_has_role_definition` | Procura uma atribuição explícita de Product Manager, aceitando variação de caixa e espaços. | Proteger a persona escolhida para Role Prompting. |
| `test_prompt_mentions_format` | Confere a instrução de Markdown ou o padrão Como/eu quero/para que antes dos exemplos. | Evitar que uma menção apenas dentro de um exemplo mascare a ausência da instrução. |
| `test_prompt_has_few_shot_examples` | Confere dois ou mais blocos de exemplo, cada um com entrada, saída, User Story e critérios de aceitação. | Verificar a presença de demonstrações utilizáveis, além do rótulo Few-shot nos metadados. |
| `test_prompt_no_todos` | Examina o conteúdo YAML da v2, incluindo metadados aninhados. | Detectar placeholders esquecidos fora do system_prompt. |
| `test_minimum_techniques` | Exige lista de nomes não vazios e duas técnicas distintas após normalizar caixa e espaços. | Evitar contar técnicas duplicadas como duas estratégias. |

As mensagens de falha indicam o campo ou o exemplo que precisa ser corrigido.
O arquivo também pode ser executado diretamente com Python e retorna o código de saída do pytest.

## Validação realizada

```bash
venv/bin/python -m pytest tests/test_prompts.py -v --tb=short
# 6 passed

venv/bin/python -m pytest tests -q
# 26 passed
```

[Saída registrada da suíte completa](requirement-5-tests.txt).

Também foram verificadas 14 variantes defeituosas em memória: system ausente,
vazio ou de tipo inválido; persona removida; formato mencionado somente em exemplo;
apenas o rótulo Few-shot; somente um exemplo; entrada vazia; bloco Saída ausente;
TODO no user_prompt ou em metadado aninhado; técnicas repetidas, vazias ou fornecidas como texto.
Todos esses defeitos foram rejeitados. O arquivo do prompt não foi modificado por essa verificação.

## Limites e relação com o requisito 4

São verificações estáticas da estrutura e das instruções do prompt, adaptadas ao formato
de exemplos usado pelo projeto. Não medem a qualidade de respostas novas, não asseguram
que o modelo obedeça às instruções e não reavaliam as notas do LangSmith.

O prompt permanece idêntico ao [snapshot da execução 11](iterations/11-prompt.yml),
que atingiu as cinco médias mínimas. Os arquivos fornecidos de avaliação,
as métricas e o dataset permanecem sem alterações.

[Revisão da execução 11](REVIEW-11.md) · [Resultados completos](iterations/11-results.json).
