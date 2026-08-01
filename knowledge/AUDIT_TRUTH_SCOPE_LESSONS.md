# Lições permanentes da reauditoria — escopo, verdade e integridade

## 1. Aprovação sempre tem escopo

Nunca usar `APPROVED`, `PASS` ou `READY_FOR_ROBLOX` sem dizer **o que exatamente foi aprovado**.

Estados permitidos nesta camada:

- `SATISFIED`: somente o escopo solicitado foi comprovado;
- `FAILED`: uma exigência do escopo falhou;
- `BLOCKED`: faltam ferramenta, dado ou evidência;
- `release_eligible=true`: permitido apenas no escopo `ugc_marketplace`, após evidência real do Studio/UGC ligada ao SHA-256 exato.

Exemplos:

- preservar a textura sem mover vértices não prova que a malha original era boa;
- um GLB que abre em um parser não prova conformidade completa com glTF 2.0;
- passar na geometria local não prova importação, animação, cages ou publicação;
- o resultado do Avatar Setup é um novo artefato e invalida a decisão do arquivo de entrada.

## 2. Métrica absoluta e métrica de regressão são diferentes

Uma correção pode adicionar zero defeitos novos e ainda manter milhares de defeitos antigos.

Todo relatório deve registrar simultaneamente:

- `absolute_output_*`: estado real do arquivo de saída;
- `delta_from_baseline_*`: mudança causada pela execução.

Nunca aprovar prontidão Roblox apenas porque `new_boundary_edge_count = 0`. Também é necessário que o número absoluto de arestas abertas permitido pelo pipeline seja zero, exceto as exceções oficialmente documentadas e semanticamente classificadas.

## 3. Mesh object não é connected component

Um único objeto de mesh pode conter dezenas ou centenas de componentes desconectados. Para Avatar Setup:

- 1 ou mais objetos de mesh podem ser aceitos;
- o corpo precisa ser contíguo, com exceções controladas para olhos e boca;
- cada componente desconectado deve constar em um manifesto semântico;
- componente `unknown`, fragmento pequeno, acessório acidental ou superfície aberta não explicada reprova a prontidão.

## 4. Double-sided não conserta geometria

`doubleSided=true` apenas permite renderizar os dois lados. Não fecha buracos, não cria espessura e não prova watertightness. Nunca usar uma aparência visual sem buracos como substituto para contagem de arestas de borda e inspeção de backfaces.

## 5. Requisitos oficiais, heurísticas e provas do Studio

### Requisitos oficiais

Devem ser citados como Roblox/Blender/Khronos e não podem ser enfraquecidos pelo agente.

### Heurísticas internas

Exemplos: 62 vistas, gutter UV de 16 px, bleed de 8 px, IoU 0,995. São políticas de qualidade do projeto e devem ser rotuladas como tal.

### Provas exclusivas do Studio/UGC

Importação, Avatar Setup, visualizações UGC, movimento, roupa em camadas, attachments, iluminação, FACS e publicação precisam de evidência produzida no Studio ou no validador UGC para o mesmo SHA-256.

## 6. Lições do GLB reavaliado

Artefato: `Meshy_AI_GLF_FINAL_R6_VISUAL_ROLLBACK_PRESERVED_v1 (2).glb`

- SHA-256: `40adc2fdf158cc7d91b3b543309ef5c58f2a87d2ded3efdd21988c3bf8ff6321`;
- 1 objeto de mesh, mas 139 componentes conectados independentes;
- 2.684 arestas abertas e 138 componentes não watertight;
- 9.764 triângulos, abaixo do total de 10.742, mas próximo o bastante para que caps gerados aumentem o risco;
- 0 skins, 0 animações e 0 morph targets — permitido como entrada básica do Avatar Setup, insuficiente como corpo final;
- frente visual `+Z`, enquanto a entrada do Avatar Setup exige `-Z`;
- matriz de nó com escala 3,25 e translação Y 3,25, não congelada;
- textura JPEG RGB 2048², sem alpha;
- UV sem sobreposição geométrica detectada, porém gutter mínimo de 0,887 px e distância à borda de 0,018 px em 2048²;
- `doubleSided=true`, que pode esconder visualmente superfícies abertas.

Conclusão: `avatar_setup_input_readiness = FAILED`; `r15_final_readiness = BLOCKED`; `studio_playtest = BLOCKED`; `ugc_marketplace = BLOCKED`.

## 7. Correção segura recomendada

Com 139 componentes e 2.684 arestas abertas, não tratar o problema como simples ajuste local. O escopo correto deve ser `full_rebuild` ou uma reconstrução controlada da entrada do Avatar Setup.

Ordem:

1. preservar o original por SHA-256;
2. separar e classificar semanticamente todos os componentes;
3. remover fragmentos e acessórios apenas com autorização;
4. reconstruir/fechar o corpo por regiões, sem Smooth global, Remesh ou Merge by Distance cegos;
5. manter olhos e partes da boca como componentes oficiais distintos;
6. corrigir frente e transformação antes de rigging;
7. reempacotar UV com padding seguro sem alterar a identidade visual;
8. reexportar e reabrir o GLB;
9. repetir auditoria absoluta, comparação visual e Avatar Setup;
10. considerar a saída do Avatar Setup um novo arquivo.
