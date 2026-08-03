# Non-Destructive Body and Face Rig Specification v2.0

## Escopo

Adicionar rig corporal e facial a um GLB preservando integralmente tudo que já passou nas auditorias anteriores.

## Locks obrigatórios

- SHA-256 do GLB fonte;
- hashes de POSITION, NORMAL, TEXCOORD_0, índices e imagens por primitive;
- bounds, triângulos, materiais e transforms;
- nenhuma mudança geométrica em `rig_only`.

## Contrato corporal

- hierarquia base: Root, HumanoidRootNode, LowerTorso, UpperTorso, Head, braços, mãos, pernas e pés;
- joints adicionais não podem quebrar a cadeia base;
- máximo 4 influências por vértice;
- soma dos pesos dentro de `1 ± 1e-5`;
- zero peso no Root e zero vértices deformáveis sem peso.

## Contrato facial

- `DynamicHead` sob `Head` e marcado como RootFaceJoint;
- olhos esquerdo e direito independentes;
- oito joints de pálpebra Roblox presentes;
- controles separados para sobrancelhas, bochechas, nariz, mandíbula, queixo, lábios e língua;
- componentes internos permanecem independentes;
- neutral/rest pose preservada;
- FACS e FaceControls são outro gate e não podem ser inferidos.

## Provas visuais

- 50 vistas externas: 10 yaws × 5 pitches;
- 50 vistas internas no mesmo conjunto angular;
- quatro vistas rotuladas dos joints faciais;
- oito vistas do rig corporal;
- mapa de joint dominante;
- poses: neutral, head yaw, elbows, knees, jaw drop, blink, smile e eyes-left.

## Decisão

- `RIGGED_LOCAL_REVIEWED`: locks, pesos, hierarquia e provas locais passam;
- `BLOCKED`: evidência ou ferramenta necessária ausente;
- `REJECTED`: hash alterado, drift, peso inválido ou joint obrigatório ausente;
- `ROBLOX_RELEASE_APPROVED`: somente após Khronos, Blender reimport, Studio e UGC aplicáveis ao hash exato.
