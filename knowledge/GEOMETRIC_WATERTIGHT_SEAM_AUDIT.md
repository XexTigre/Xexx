# Auditoria geométrica versus costuras de renderização

## Regra central

Uma malha glTF pode duplicar vértices na mesma posição para armazenar UVs, normais ou tangentes diferentes. Esses vértices duplicados podem fazer uma auditoria baseada apenas em índices declarar milhares de arestas abertas, embora a superfície geométrica coincida perfeitamente.

Por isso, toda auditoria deve produzir dois resultados separados:

1. `render_index_topology`: usa os índices reais do arquivo e detecta divisões de atributos;
2. `geometric_position_topology`: consolida somente posições exatamente iguais ou dentro de tolerância bloqueada e mede buracos físicos.

Nunca converter automaticamente `render_index_boundary_edges > 0` em `NOT_WATERTIGHT` sem executar a segunda análise.

## Caso de regressão

No arquivo de origem desta personagem:

- vértices de renderização: 6.363;
- triângulos: 9.764;
- componentes por índices de renderização: 139;
- arestas abertas por índices de renderização: 2.684;
- vértices geométricos após consolidação de posições idênticas: 4.932;
- componentes geométricos: 25;
- arestas abertas geométricas: 0;
- arestas non-manifold geométricas: 0.

Conclusão: a maior parte dos 139 componentes e das 2.684 arestas vinha de costuras de UV/normais, não de buracos físicos.

## Limites de segurança

- A consolidação usada para auditoria não autoriza alterar o GLB.
- Não soldar vértices de UV globalmente no artefato final, pois isso pode destruir costuras e pintura.
- Registrar a tolerância usada; o padrão preferido é igualdade de posição após quantização determinística de alta precisão.
- Se a solda por posição gerar faces degeneradas, non-manifold ou unir regiões próximas sem correspondência semântica, o resultado fica `BLOCKED`.
- Watertightness geométrica não prova contiguidade semântica do corpo nem prontidão no Avatar Setup.

## Reparo aprovado para este caso

Foi gerado `RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb` com:

- frente `-Z` e `+Y` para cima;
- transformações de nós em identidade;
- textura JPEG original preservada byte a byte;
- 9.864 triângulos, margem de 878 antes dos caps;
- cílios geométricos removidos do corpo e colocados em arquivo de acessório separado;
- dois olhos separados;
- mouthbag, dentes superiores, dentes inferiores e língua independentes;
- ajuste localizado do pescoço sem Smooth global ou Remesh;
- todos os nós geometricamente fechados após auditoria por posição;
- IoU mínimo de silhueta em 12 azimutes: 0,995506.

O estado correto é `CANDIDATE_LOCAL_REVIEWED`. Khronos Validator, Avatar Setup e Roblox Studio permanecem `NOT_RUN`.

## Fontes

- Roblox Avatar Setup specifications: https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- Roblox character body specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
- Khronos glTF Validator: https://github.com/KhronosGroup/glTF-Validator
