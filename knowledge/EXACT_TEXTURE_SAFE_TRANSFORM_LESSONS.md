# Lições permanentes — textura exata e transformação segura

## Regra central

`TEXTURE_EXACT=PASS` significa somente que os bytes da imagem incorporada, os UVs e a topologia protegida permaneceram idênticos. Não significa que o modelo está pronto para Avatar Setup, corpo R15 final, Roblox Studio ou Marketplace.

## Três identidades independentes

Todo job de preservação deve calcular e comparar separadamente:

1. SHA-256 da imagem incorporada;
2. SHA-256 das coordenadas `TEXCOORD_0`;
3. SHA-256 dos índices dos triângulos.

A textura só pode ser chamada de `byte-exata` quando o hash da imagem for idêntico. O UV só pode ser chamado de preservado quando seu próprio hash for idêntico. A topologia só pode ser chamada de preservada quando os índices e contagens forem idênticos.

## Transformações permitidas

Uma correção de eixo ou escala pode ser executada sem deformar a identidade quando:

- o transform original é aplicado matematicamente aos vértices;
- normals usam inversa transposta e são renormalizadas;
- tangentes são transformadas e renormalizadas;
- UVs, índices, imagem e material não são reempacotados nem recodificados;
- o nó exportado termina com transform identidade;
- o artefato é reaberto e comparado ao original.

Uma rotação rígida de 180° em Y pode produzir uma variante `-Z` para tentativa de Avatar Setup sem alterar distâncias internas, UV ou textura. Ela não corrige buracos, componentes desconectados, head internals ou ausência de rig.

## Não propagar aprovação

- `TEXTURE_EXACT=PASS` não implica `GEOMETRY=PASS`.
- `TRANSFORM_BAKED=PASS` não implica `AVATAR_SETUP_READY`.
- `FRONT_AXIS=-Z` não implica corpo contíguo ou watertight.
- `TRIANGLES<=10742` não implica que caps gerados manterão o ativo no orçamento.
- imagens multiview não substituem Avatar Setup, Check Body, Check Face ou UGC Validation.

## Caso de regressão aceito

Fonte: `Meshy_AI_GLF_FINAL_R6_VISUAL_ROLLBACK_PRESERVED_v1 (2).glb`

- SHA-256 da fonte: `40adc2fdf158cc7d91b3b543309ef5c58f2a87d2ded3efdd21988c3bf8ff6321`;
- textura incorporada: `193701f1f7d3c85f16da09d0ce8b26b8c0c85ed6771d694eabd62be73faa35a6`;
- UV: `1110a2d175a85775ec398f07879b2e275ae70b47995ec2bcdedbbcafe6e3f98a`;
- índices: `9e9fd8befd6fd2b946386e0b0d1ea8466d46dae4d2a3363c6a7c2b981165023f`.

Saídas:

- `RBX_ANIME_DOLL_PRESERVED_PLUSZ_BAKED.glb` — SHA-256 `264718e251aec72081f5179504d62ec6771fe7782d5930d4d3718b67bf1288f6`;
- `RBX_ANIME_DOLL_AVATAR_SETUP_NEGZ_BAKED.glb` — SHA-256 `b3b5bcb4fa0f1cb7574bd242e24ea9e6b9fae9289c192a6d77dc979ebc2317e7`.

Nas duas saídas, imagem, UV e índices mantiveram hashes idênticos. Mesmo assim, a prontidão permaneceu `FAIL/BLOCKED` por 139 componentes desconectados, 2.684 arestas abertas, ausência de rig/cages/attachments e falta de teste no Studio.

## Fontes oficiais

- Roblox Avatar Setup requirements: https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- Roblox character-body specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
- Roblox Avatar Setup testing: https://create.roblox.com/docs/avatar-setup
- Khronos glTF Validator: https://github.com/KhronosGroup/glTF-Validator
