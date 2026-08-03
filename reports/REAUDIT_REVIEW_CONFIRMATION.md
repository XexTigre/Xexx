# Confirmação de revisão independente — v1.3.0

## Revisão 1 — fatos e autoridade

Confirmado:

- requisitos do Avatar Setup foram separados dos requisitos do corpo R15 final;
- ausência de rig foi tratada como permitida para entrada básica e insuficiente para corpo final;
- `1 mesh object` não foi confundido com `1 connected component`;
- 62 vistas e padding UV foram rotulados como política interna, não como exigência oficial;
- prova de Studio/UGC permaneceu `BLOCKED` porque não foi executada;
- o Khronos glTF Validator permaneceu `NOT_RUN`, sem falso PASS.

## Revisão 2 — resistência a alegações fabricadas

O primeiro schema permitia declarar contagens resumidas de componentes sem listar os componentes. A revisão corrigiu isso exigindo `component_manifest`, cruzando:

- tamanho do manifesto × connected components;
- componentes classificados × desconhecidos;
- soma das arestas abertas não autorizadas;
- classes permitidas para exceções de olhos e boca;
- evidência semântica para pose, pescoço, componentes faciais e ausência de acessórios.

## Revisão 3 — execução

- JSON Schema Draft 2020-12: válido;
- exemplo do GLB atual: válido contra o schema;
- YAML: válido;
- Python: compilado;
- testes adversariais: 11 aprovados;
- execução no GLB atual: `FAILED` para `avatar_setup_input_readiness`;
- `release_eligible`: false.

## Limite honesto

A auditoria local mede o container, inventário, geometria, UV e metadados do GLB. Ela não substitui o relatório oficial do Khronos Validator nem os resultados do Roblox Studio e do UGC Validator.
