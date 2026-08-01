# Safe Topology Repair Specification v1.5

## 1. Objetivo

Corrigir fragmentação, arestas abertas e ausência de contiguidade sem suavizar, remesclar ou deformar globalmente a personagem.

## 2. Entrada obrigatória

- artefato original e SHA-256;
- artefato de trabalho em cópia;
- pipeline `avatar_setup_body_input`;
- baseline geométrico, visual, UV e de textura;
- manifesto completo de componentes;
- máscara de edição por região;
- lista de operações autorizadas.

## 3. Fases obrigatórias

### Fase A — Inventário

Separar logicamente todos os componentes conectados e registrar ID, contagens, bounds, material, arestas abertas e classificação semântica.

Saída obrigatória: zero componentes sem ID.

### Fase B — Classificação

Classificar cada componente como corpo, olho esquerdo, olho direito, mouthbag, dentes superiores, dentes inferiores, língua, roupa autorizada, acessório, fragmento ou desconhecido.

Saída obrigatória: zero componentes `unknown` antes do reparo final.

### Fase C — Quarentena

Componentes classificados como fragmento ou acessório não permitido devem ser movidos para quarentena. Não apagar definitivamente antes da comparação visual.

### Fase D — Reparo local

- Grid Fill para loops pequenos e fechados;
- Bridge Edge Loops para pares de loops correspondentes;
- retopologia local para aberturas grandes ou irregulares;
- Shrinkwrap, quando autorizado, somente nos novos vértices e limitado por vertex group;
- sem Smooth, Remesh, Decimate, Weld ou Merge by Distance global.

### Fase E — Transferência visual

A imagem de textura pode permanecer byte-exata. Novas faces devem receber UVs por transferência/projeção local e ser verificadas por checker, seam heatmap e comparação por pixel.

Mudança topológica invalida qualquer alegação de UV byte-exato.

### Fase F — Reabertura e auditoria

Reabrir o GLB exportado e medir:

- componentes conectados absolutos;
- arestas de borda absolutas por componente;
- non-manifold;
- self-intersections;
- triângulos;
- eixo frontal;
- transformações;
- textura, UV e costuras;
- silhueta e volume fora das máscaras.

## 4. Requisitos de saída para Avatar Setup

- corpo principal contíguo;
- zero arestas abertas no corpo principal;
- exceções faciais limitadas aos componentes necessários;
- dois olhos independentes;
- mouthbag, dentes superiores, dentes inferiores e língua independentes;
- A-pose ou T-pose;
- frente `-Z`;
- pescoço distinto;
- sem acessórios não permitidos;
- até 10.742 triângulos após o reparo e com margem para caps;
- textura sem vazamento novo.

## 5. Locks de identidade

Fora das máscaras autorizadas:

- delta de vértice máximo: `1e-5` stud;
- silhouette IoU mínimo: `0.995`;
- contour Chamfer p95 máximo: `1 px` em 1024;
- volume relativo: `0.995–1.005`;
- zero novas interseções;
- zero novas arestas non-manifold.

Os números desta seção são políticas internas do projeto.

## 6. Operações proibidas por padrão

- `global_smooth`;
- `voxel_remesh`;
- `remesh_apply`;
- `decimate_apply_global`;
- `merge_by_distance_global`;
- `weld_global`;
- `boolean_global`;
- `fill_all_holes_automatic`;
- `delete_small_components_automatic`;
- `apply_armature_transform_after_binding`;
- `automatic_weights_as_final`.

## 7. Decisão

- `BLOCKED`: falta manifesto, classificação, máscara, ferramenta ou evidência.
- `REJECTED`: houve deformação fora da máscara, componente desconhecido, buraco não explicado, operação proibida ou hash adulterado.
- `READY_FOR_AVATAR_SETUP_INPUT`: todos os requisitos desta spec foram comprovados.

Este estado não equivale a corpo R15 final ou aprovação de Marketplace.