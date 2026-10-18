# Histórico de iterações

As cinco médias atingiram a meta de 0.8. Foi realizada somente uma nova avaliação, aguardando revisão manual.

[Dataset e experimentos públicos](https://smith.langchain.com/public/843ce0f5-2616-4911-bfe6-ab30c3f9c85d/d).

| Iteração | Helpfulness | Correctness | F1 | Clarity | Precision | Média | Aprovado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [01](01-results.json) | 0.8322 | 0.8351 | 0.7697 | 0.7640 | 0.9005 | 0.8203 | Não |
| [02](02-results.json) | 0.8133 | 0.7612 | 0.6718 | 0.7760 | 0.8507 | 0.7746 | Não |
| [03](03-results.json) | 0.8184 | 0.7762 | 0.6790 | 0.7635 | 0.8733 | 0.7821 | Não |
| [04](04-results.json) | 0.8378 | 0.7887 | 0.6940 | 0.7922 | 0.8833 | 0.7992 | Não |
| [05](05-results.json) | 0.7659 | 0.7771 | 0.7395 | 0.7172 | 0.8147 | 0.7629 | Não |
| [06](06-results.json) | 0.7703 | 0.8064 | 0.7914 | 0.7193 | 0.8213 | 0.7817 | Não |
| [07](07-results.json) | 0.7982 | 0.8114 | 0.7775 | 0.7510 | 0.8453 | 0.7967 | Não |
| [08](08-results.json) | 0.7636 | 0.7176 | 0.6384 | 0.7303 | 0.7969 | 0.7294 | Não |
| [09](09-results.json) | 0.8450 | 0.8263 | 0.7632 | 0.8007 | 0.8893 | 0.8249 | Não |
| [10](10-results.json) | 0.8344 | 0.8325 | 0.7702 | 0.7742 | 0.8947 | 0.8212 | Não |
| [11](11-results.json) | 0.8463 | 0.8448 | 0.8070 | 0.8100 | 0.8827 | 0.8382 | Sim |

## Alterações por execução

- [01: prompt](01-prompt.yml) — Versão inicial com Few-shot Learning e Role Prompting. Commit `eeab945b46f9853c06dcd90ffed38d94cedc4efed319d057041174fe61b88d7d`.
- [02: prompt](02-prompt.yml) — Metas explícitas, critérios verificáveis e orientações de concisão. Commit `6d593bf62b198876d9336ac760484602ef55a63d9d6963338f2800e33ff6b698`.
- [03: prompt](03-prompt.yml) — Instruções simplificadas, limites exatos e acessibilidade. Commit `7a068950e226662f059eff96f6dab24c3764cdda6460bed753c090d40df974e7`.
- [04: prompt](04-prompt.yml) — Cobertura funcional de validação, webhooks, permissões e desempenho. Commit `b63fcfa64972c2674a37422550d52366201dfa4d96d883b04c55e4b7a29836d8`.
- [05: prompt](05-prompt.yml) — Formato direto, exemplos menores e contexto técnico obrigatório. Commit `7366927219fd991011b98bfd913d9865ee9128839737200951a76356b4a635f7`.
- [06: prompt](06-prompt.yml) — Uma especificação por produto; geração com raciocínio high. Commit `2de03254fafe208fcc57c368de9a2d0a0069040b381f11f9510aafe402d6560e`.
- [07: prompt](07-prompt.yml) — Mesmo prompt da 06; juiz com raciocínio high e JSON exigido pela API. Commit `2de03254fafe208fcc57c368de9a2d0a0069040b381f11f9510aafe402d6560e`.
- [08: prompt](08-prompt.yml) — Critérios no futuro, comportamento após a correção e verbosidade low na geração. Commit `51e3e9ce19d961469345e5847a621bb7129337cadb5ca9b33a408cf50dc2cac3`.
- [09: prompt](09-prompt.yml) — Reprodução exata da configuração 01: manifesto idêntico, gpt-5-nano nos dois papéis, padrões do provedor e concorrência 1. Commit `621ec080979f5c2486b5cfb7abd500587dc1e39fd9343a44627e7da8868d4add`.
- [10: prompt](10-prompt.yml) — Preservação de estados e restrição de requisitos adicionais; demais configurações iguais à 09. Commit `c7474269af12399be238bc1fffe3f3c64478d2038a53c4321f481bc73da3d518`.
- [11: prompt](11-prompt.yml) — Critérios gerais para contagem e filtro ativo, preservação do contexto técnico e critérios separados para listas com travamento. Demais configurações iguais à 10. Commit `44b0d9e43de7a18eb1acd10283bb1801749ba701bd736dd91388909c0db41577`.

As execuções 01–05 usam o raciocínio padrão do provedor. A 06 usa high somente na geração. A 07 usa high nos dois papéis e JSON no juiz. A 08 mantém essa configuração e usa verbosidade low na geração. A 09 restaura a configuração completa da 01, incluindo concorrência 1. A 10 mantém essa configuração e altera somente o prompt. Os modelos permanecem gpt-5-nano em todas as execuções.

Os relatórios preservam todas as notas, inclusive as baixas e as decorrentes de falha no parser. As notas não foram editadas manualmente. A aprovação usa médias por métrica; notas individuais podem ficar abaixo de 0.8. Não foi criado conjunto de teste independente.

[Guia de revisão manual](../REVIEW.md).


[Revisão da execução 10](../REVIEW-10.md) · [Comparação 09 × 10](10-comparison.json).

[Revisão da execução 11](../REVIEW-11.md) · [Comparação 10 × 11](11-comparison.json).
