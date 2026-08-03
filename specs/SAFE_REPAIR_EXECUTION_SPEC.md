# Safe Repair Execution Specification v1.6

## Objetivo

Executar reparos de entrada do Avatar Setup sem deformação global e sem confundir costuras UV com buracos físicos.

## Entradas obrigatórias

- arquivo-fonte e SHA-256;
- pipeline `avatar_setup_body_input`;
- frente `-Z`, cima `+Y`;
- baseline de silhueta, textura, UV, componentes e transforms;
- manifesto semântico de componentes;
- lista bloqueada de operações autorizadas.

## Auditoria dupla de topologia

### Render-index topology

Mede componentes e arestas usando os índices exatos do glTF. Serve para detectar fragmentação de atributos e costuras.

### Geometric-position topology

Consolida somente vértices com posição idêntica segundo quantização determinística e mede:

- componentes geométricos;
- arestas abertas físicas;
- arestas non-manifold;
- faces degeneradas criadas pela consolidação.

Uma falha em render-index topology não reprova watertightness física sozinha.

## Operações permitidas neste caso

- separar semanticamente meshes sem mover vértices;
- retirar cílios/sobrancelhas geométricos do corpo e preservá-los como acessório separado;
- preservar olhos como componentes independentes;
- adicionar mouthbag, dentes superiores, dentes inferiores e língua como geometria oculta de baixo polycount;
- subdivisão linear localizada no pescoço, sem deslocar a superfície pela média dos vizinhos;
- ajuste local bloqueado por parâmetros explícitos;
- reutilizar a imagem JPEG original sem recodificação;
- reabrir e medir o GLB exportado.

## Operações proibidas

- Smooth global;
- Voxel Remesh ou Remesh;
- Merge by Distance ou Weld global;
- Boolean global;
- Decimate global;
- apagar componentes por tamanho sem classificação;
- converter contagem de costuras em prova de buraco;
- declarar aprovação do Avatar Setup ou Studio sem execução real.

## Gates quantitativos internos

- triângulos totais `<= 10.742`;
- margem recomendada antes dos caps `>= 500`;
- transforms dos nós em identidade;
- textura original byte-exata quando não houver pintura nova;
- todos os nós com zero arestas abertas e zero non-manifold na auditoria geométrica por posição;
- IoU mínimo de silhueta em 12 azimutes `>= 0,995`;
- nenhuma alteração fora das regiões autorizadas.

Esses thresholds de preservação são políticas internas, não limites oficiais adicionais da Roblox.

## Estados

- `CANDIDATE_LOCAL_REVIEWED`: passou estrutura local, hashes, orçamento, silhueta e auditoria geométrica;
- `REJECTED`: alterou região protegida, excedeu orçamento, introduziu buraco físico ou adulterou evidência;
- `BLOCKED`: falta ferramenta, classificação ou prova;
- `READY_FOR_AVATAR_SETUP_INPUT`: somente após todas as exigências do modelo e revisão humana estarem comprovadas;
- `READY_FOR_ROBLOX`: proibido sem saída do Avatar Setup e evidência real do Studio/UGC.

## Caso v1.6

`RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb`:

- SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`;
- 9.864 triângulos;
- margem: 878;
- textura JPEG byte-exata;
- transforms identidade;
- nós geometricamente watertight;
- IoU mínimo: 0,995506;
- Avatar Setup/Studio/Khronos: `NOT_RUN`.
