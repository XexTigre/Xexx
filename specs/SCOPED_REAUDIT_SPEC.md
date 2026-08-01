# Scoped Reaudit Specification v1.3

## Objetivo

Impedir que resultados parciais sejam promovidos a aprovação global e garantir que cada nova auditoria diferencie conformidade absoluta, preservação e prova de execução no Roblox Studio.

## Escopos

1. `container_parse` — cabeçalho GLB, chunks, JSON e buffers legíveis.
2. `gltf_spec_validation` — relatório do Khronos glTF Validator.
3. `preservation` — somente diferenças baseline × saída.
4. `avatar_setup_input_readiness` — requisitos da entrada do Avatar Setup.
5. `r15_final_readiness` — corpo final R15 completo.
6. `studio_playtest` — importação e testes funcionais no Studio.
7. `ugc_marketplace` — validação UGC real para publicação.

## Regra de não propagação

Um escopo inferior nunca aprova automaticamente um escopo superior. `container_parse=SATISFIED` não implica `gltf_spec_validation`, e `preservation=SATISFIED` não implica `r15_final_readiness`.

## Avatar Setup input

Exige, entre outros:

- um ou mais objetos de mesh;
- até 10.742 triângulos no total;
- forma humanoide em A-pose ou T-pose;
- frente `-Z`, corpo centrado no eixo Y;
- pescoço distinto;
- nenhum acessório incorporado;
- textura presente;
- olhos e componentes da boca configurados;
- corpo contíguo e watertight, exceto exceções oficiais classificadas;
- zero componentes desconhecidos no manifesto semântico.

Rigging não é obrigatório para a entrada básica.

## Corpo R15 final

Exige, entre outros:

- 15 meshes corporais nomeadas;
- frente `+Z`, cima `+Y`;
- transformações congeladas e pivôs corretos;
- partes fechadas e caps próprios;
- rig e skinning válidos;
- no máximo quatro influências por vértice e zero no Root;
- 15 outer cages e 19 attachments;
- evidência de importação e testes no Studio antes de publicação.

## Evidência semântica

Cada evidência inclui tipo e `subject_ids`. Uma captura genérica não prova todas as poses. Uma evidência de pose deve declarar a pose específica; uma evidência do Studio deve declarar o gate específico.

## Métricas absolutas

Todo audit document registra o estado absoluto da saída: componentes, arestas abertas, non-manifold, triângulos, transforms, rig, cages e attachments. Métricas `new_*` são apenas regressão e não substituem o estado absoluto.

## Autoridade

- `official`: regra publicada por Roblox, Blender, Khronos ou padrão técnico;
- `project`: threshold de qualidade interno;
- `studio_only`: só pode ser comprovado no Studio/UGC.

Uma falha de heurística interna é reportada separadamente; o agente não pode apresentá-la como regra oficial.
