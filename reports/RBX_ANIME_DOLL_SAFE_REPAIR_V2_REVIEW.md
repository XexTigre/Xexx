# Revisão — Safe Repair V2

Artefato: `RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb`

SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`

Estado: `CANDIDATE_LOCAL_REVIEWED`.

## Estrutura

- GLB 2.0 e intervalos de buffers: PASS.
- Reabertura local: PASS.
- Transformações de nós em identidade: PASS.
- Frente -Z e cima +Y.

## Geometria

- 9.864 triângulos.
- Margem de 878 antes dos caps.
- Todos os nós sem arestas abertas físicas após consolidação de posições idênticas.
- Todos os nós sem arestas non-manifold físicas.

A contagem antiga de 2.684 arestas abertas era principalmente causada por vértices duplicados em costuras UV e normais, não por buracos físicos.

## Preservação

- JPEG incorporado byte-exato.
- Pixels decodificados idênticos.
- IoU mínimo da silhueta em 12 azimutes: 0,995506.
- IoU médio: 0,998022.

## Mudanças locais

- cílios geométricos retirados do corpo e preservados em acessório separado;
- olhos separados preservados;
- mouthbag, dentes superiores, dentes inferiores e língua adicionados;
- pescoço recebeu subdivisão linear localizada e ajuste controlado;
- nenhum Smooth global, Remesh, Decimate, Weld ou Boolean global.

## Limites

Khronos Validator, Avatar Setup, Roblox Studio e UGC Validator não foram executados. `release_eligible=false`.
