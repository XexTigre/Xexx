# Reparo seguro de componentes e buracos sem deformar a personagem

## Caso de referência

Artefato de origem: `Meshy_AI_GLF_FINAL_R6_VISUAL_ROLLBACK_PRESERVED_v1 (2).glb`

Falhas conhecidas:

- 139 componentes conectados independentes;
- 2.684 arestas de borda;
- 138 componentes não watertight;
- frente originalmente em `+Z`, enquanto a entrada do Avatar Setup usa `-Z`;
- rig, cages e attachments ausentes;
- componentes internos da cabeça ainda sem classificação semântica.

## Princípio central

Não usar limpeza automática global. O reparo deve ser feito por componente, por loop de borda e por máscara de edição. A malha original permanece imutável e é usada como referência de silhueta, volume, textura e identidade.

## O que as regras Roblox exigem

Para entrada corporal do Avatar Setup:

- corpo humanoide em A-pose ou T-pose;
- frente em `-Z`;
- corpo contíguo e watertight, exceto olhos e boca;
- pescoço distinto;
- sem cabelo, cílios, sobrancelhas, barba ou outros acessórios incorporados;
- dois olhos independentes;
- mouthbag contendo dentes superiores, dentes inferiores e língua como componentes independentes;
- total de até 10.742 triângulos, considerando que o Avatar Setup pode adicionar caps.

Para corpo R15 final:

- 15 partes corporais nomeadas;
- cada parte fechada e com cap próprio;
- frente `+Z`, cima `+Y`;
- transformações congeladas e pivôs em `0,0,0`;
- rig, skinning, outer cages e 19 attachments.

Fontes:

- https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- https://create.roblox.com/docs/avatar/character-bodies/specifications
- https://create.roblox.com/docs/avatar/character-bodies

## Estratégia correta para os 139 componentes

### 1. Gerar inventário sem modificar a malha

Usar seleção ligada ou separar temporariamente por partes soltas para identificar cada componente. `Separate > By Loose Parts` cria um objeto por fragmento desconectado; `Select Linked` permite selecionar apenas a geometria conectada sob o cursor.

Registrar para cada componente:

- ID estável;
- número de vértices, faces e triângulos;
- bounds e centro;
- área e volume quando calculável;
- número de arestas de borda;
- material;
- região corporal aproximada;
- classificação semântica;
- decisão `KEEP`, `REBUILD`, `REMOVE` ou `REVIEW`.

Classificações permitidas:

- `body_shell`;
- `left_eye`;
- `right_eye`;
- `mouthbag`;
- `upper_teeth`;
- `lower_teeth`;
- `tongue`;
- `authorized_clothing`;
- `accessory`;
- `fragment`;
- `unknown`.

Nenhuma decisão pode ser `APPROVED` enquanto houver componente `unknown`.

Fontes Blender:

- https://docs.blender.org/manual/en/latest/modeling/meshes/selecting/linked.html
- https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/separate.html

### 2. Preservar os componentes faciais obrigatórios

Não unir olhos, dentes ou língua ao corpo. O Avatar Setup exige olhos separados e mouthbag com dentes superiores, inferiores e língua sem compartilhamento de vértices com a cabeça ou entre si.

O objetivo não é transformar tudo em um único componente. O objetivo é deixar o corpo principal contíguo e manter apenas as exceções faciais oficialmente permitidas.

### 3. Remover somente fragmentos comprovados

Um componente pequeno não é automaticamente lixo. Antes de remover:

- confirmar que não pertence a olho, pálpebra, boca, dentes, língua, unha ou detalhe visível;
- comparar renders antes/depois em 12 ou 62 vistas;
- confirmar que a silhueta não mudou fora da máscara;
- registrar o ID do componente e a justificativa;
- manter cópia do componente removido em uma coleção de quarentena.

Não usar remoção por tamanho global.

### 4. Fechar buracos de modo localizado

Cada loop de borda deve ser classificado antes do reparo.

#### Loop pequeno e fechado

Usar `Grid Fill` quando o contorno admitir uma grade previsível. O Blender recomenda loops opostos com números iguais de vértices para o resultado mais previsível.

#### Dois loops correspondentes

Usar `Bridge Edge Loops` para conectar os loops, verificando twist, número de cortes e interpolação. Preferir loops com contagem de vértices compatível.

#### Abertura irregular grande

Não usar Fill indiscriminado. Reconstruir localmente a superfície em quads, mantendo o original congelado como referência. Se Shrinkwrap for usado, deve atuar somente nos novos vértices, com vertex group local, limite de distância e comparação antes/depois. Não aplicar Shrinkwrap globalmente.

Fontes Blender:

- https://docs.blender.org/manual/en/latest/modeling/meshes/editing/face/grid_fill.html
- https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bridge_edge_loops.html
- https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/cleanup.html

### 5. Não usar operações destrutivas globais

Proibido por padrão neste caso:

- Voxel Remesh;
- Remesh;
- Decimate global;
- Merge by Distance global;
- Weld global;
- Boolean global;
- Smooth global;
- Fill Holes automático em todos os loops;
- excluir todos os loose parts pequenos;
- aplicar transformações depois de rigar;
- pesos automáticos considerados como resultado final.

Booleans em geometria não-manifold podem produzir artefatos e resultados imprevisíveis. O arquivo atual possui milhares de arestas abertas, portanto Boolean não deve ser a primeira ferramenta de reparo.

## Preservação da textura durante mudança de topologia

A imagem JPEG incorporada pode continuar byte-exata. Porém, quando novos vértices e faces são criados, o hash do UV completo necessariamente muda. Portanto:

- não declarar `UV_EXACT=PASS` após reconstrução topológica;
- declarar apenas `TEXTURE_IMAGE_BYTE_EXACT=PASS` quando o arquivo de imagem for idêntico;
- transferir UVs e custom normals da superfície original para as novas regiões usando Data Transfer ou projeção local;
- preferir mapeamento interpolado por face para superfícies correspondentes;
- revisar manualmente todas as novas ilhas e costuras;
- executar checker UV, seam heatmap e comparação de cor por pixel.

O Data Transfer usa mapeamento entre elementos e interpolação; ele é uma ferramenta de transferência, não uma prova automática de correção.

Fonte:

- https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/data_transfer.html

## Ordem segura de execução para este arquivo

1. Congelar o GLB original por SHA-256.
2. Reabrir a variante `-Z` com transform identidade.
3. Gerar inventário dos 139 componentes.
4. Identificar corpo principal, dois olhos, mouthbag, dentes superiores, dentes inferiores e língua.
5. Colocar acessórios e fragmentos em quarentena, sem excluir definitivamente.
6. Mapear todos os loops de borda por região corporal.
7. Corrigir primeiro pescoço, cabeça, tronco e junções de membros.
8. Fechar loops pequenos com Grid Fill e pares de loops com Bridge Edge Loops.
9. Retopologizar apenas aberturas grandes e irregulares.
10. Preservar a imagem de textura; transferir UVs somente para faces novas.
11. Recalcular normals e revisar backfaces.
12. Reabrir o GLB exportado e medir valores absolutos.
13. Exigir corpo principal com zero arestas abertas fora das exceções faciais.
14. Exigir zero componentes `unknown`.
15. Confirmar A-pose/T-pose, pescoço distinto, frente `-Z` e simetria central.
16. Verificar orçamento após caps; não confiar apenas nos 9.764 triângulos originais.
17. Executar Avatar Setup com alinhamento manual da frente se necessário.
18. Tratar a saída do Avatar Setup como novo artefato e repetir todas as validações.

## Gates de não deformação

Política interna do projeto:

- zero vértices movidos fora da máscara de edição acima de `1e-5` stud;
- silhouette IoU fora da máscara `>= 0.995`;
- contour Chamfer p95 fora da máscara `<= 1 px` em render 1024;
- razão de volume fora das regiões reconstruídas entre `0.995` e `1.005`;
- zero novas self-intersections;
- zero novas arestas non-manifold;
- imagem de textura com SHA-256 idêntico quando preservação byte-exata for solicitada;
- zero componentes `unknown`;
- zero arestas de borda no corpo principal fora das exceções de olhos e boca.

Esses limites são políticas internas, não limites oficiais Roblox.

## Resultado esperado

A primeira meta é produzir uma entrada válida para Avatar Setup, não um corpo R15 final manual.

O estado só pode avançar para `AVATAR_SETUP_INPUT_READY` quando:

- o corpo principal estiver contíguo;
- as únicas partes desconectadas forem os componentes faciais necessários e autorizados;
- todas as aberturas estiverem classificadas e corrigidas;
- o pescoço estiver distinto;
- a pose e o eixo estiverem corretos;
- o orçamento final estiver dentro do limite;
- a textura não apresentar novas costuras ou vazamentos.

Rig, cages, attachments, 15 partes e prova de Studio continuam sendo uma etapa posterior.