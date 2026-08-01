# Revisão confirmada — RBX_ANIME_DOLL_PRESERVED_BAKED_V2

## Artefatos

- `RBX_ANIME_DOLL_PRESERVED_PLUSZ_BAKED.glb`
  - SHA-256: `264718e251aec72081f5179504d62ec6771fe7782d5930d4d3718b67bf1288f6`
  - finalidade: preservação visual em orientação `+Z`, com transform do nó congelado;
- `RBX_ANIME_DOLL_AVATAR_SETUP_NEGZ_BAKED.glb`
  - SHA-256: `b3b5bcb4fa0f1cb7574bd242e24ea9e6b9fae9289c192a6d77dc979ebc2317e7`
  - finalidade: tentativa de entrada do Avatar Setup em `-Z`, sem alegação de prontidão.

## Preservação confirmada

- textura JPEG: `193701f1f7d3c85f16da09d0ce8b26b8c0c85ed6771d694eabd62be73faa35a6` em fonte e duas saídas;
- UV: `1110a2d175a85775ec398f07879b2e275ae70b47995ec2bcdedbbcafe6e3f98a` em fonte e saídas;
- índices: `9e9fd8befd6fd2b946386e0b0d1ea8466d46dae4d2a3363c6a7c2b981165023f` em fonte e saídas;
- transformações dos nós após reabertura: identidade;
- dimensões: `3.349859 × 6.500000 × 1.092715` studs;
- vértices: 6.363;
- triângulos: 9.764.

## Falhas preservadas e expostas

- componentes desconectados: 139;
- arestas abertas: 2.684;
- non-manifold: 0;
- head internals não classificados semanticamente;
- rig, cages e attachments ausentes;
- Roblox Studio, Avatar Setup e UGC Validator não executados.

## Decisão

- `texture_preservation = PASS`;
- `uv_preservation = PASS`;
- `topology_preservation = PASS`;
- `rigid_transform_only = PASS`;
- `avatar_setup_readiness = FAIL`;
- `r15_final_readiness = BLOCKED`;
- `release_eligible = false`.

A textura está comprovadamente inalterada em bytes. Isso não corrige nem oculta os defeitos geométricos do arquivo-fonte.
