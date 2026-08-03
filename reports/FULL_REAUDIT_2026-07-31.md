# Reauditoria completa — 2026-07-31

## Artefato

- Arquivo: `Meshy_AI_GLF_FINAL_R6_VISUAL_ROLLBACK_PRESERVED_v1 (2).glb`
- SHA-256: `40adc2fdf158cc7d91b3b543309ef5c58f2a87d2ded3efdd21988c3bf8ff6321`
- Tamanho: 2580116 bytes

## Resultado por escopo

| Escopo | Resultado |
|---|---|
| Leitura do container GLB | SATISFIED por parser local |
| Conformidade glTF 2.0 pelo Khronos Validator | BLOCKED — ferramenta oficial não executada neste ambiente |
| Entrada do Avatar Setup | FAILED |
| Corpo R15 final | BLOCKED/FAILED estrutural |
| Teste no Roblox Studio | BLOCKED — não executado |
| Validação UGC/Marketplace | BLOCKED — não executada |

## Inventário medido

- GLB 2.0, comprimento declarado igual ao arquivo;
- 1 cena, 1 nó, 1 objeto de mesh, 1 primitive;
- 6.363 vértices e 9.764 triângulos;
- 139 componentes desconectados;
- 2.684 arestas abertas;
- 0 arestas non-manifold;
- 0 triângulos degenerados e 0 triângulos duplicados detectados;
- 1 componente watertight e 138 componentes abertos;
- 0 skins, 0 animações e 0 morph targets;
- bounds: 3,349859 × 6,5 × 1,092715;
- textura JPEG RGB 2048×2048;
- UV: 0 pares de sobreposição geométrica, gutter mínimo 0,887 px e borda mínima 0,018 px em 2048²;
- material `doubleSided=true`;
- transformação de nó não identidade: escala 3,25 e translação Y 3,25;
- frente visual observada em `+Z`.

## Confronto com requisitos atuais

O Avatar Setup aceita um ou mais objetos de mesh e não exige rig para a entrada básica. Porém, exige corpo humanoide em A/T pose, frente `-Z`, corpo contíguo, watertight exceto olhos/boca, pescoço distinto, ausência de acessórios e componentes faciais específicos. O arquivo falha claramente em frente, continuidade e superfícies abertas; pose e semântica dos 139 componentes não podem ser comprovadas pelo GLB.

O corpo R15 final exige 15 meshes, frente `+Z`, cima `+Y`, transformações congeladas, partes fechadas, rig, cages e attachments. O arquivo não possui essas estruturas e não deve ser chamado de corpo final.

## Correção da auditoria anterior

- O limite de 16 px de gutter, 8 px de bleed e as 62 vistas são **políticas internas**, não limites oficiais Roblox.
- Transform identity para entrada do Avatar Setup é mantido como política estrita de estabilidade; a exigência oficial explícita de transformações congeladas pertence ao corpo final e às especificações gerais de exportação.
- `no new boundary edges` não basta. A prontidão exige analisar o número absoluto de arestas abertas.
- `1 mesh` não significa `1 componente contíguo`.
- `doubleSided=true` não prova geometria fechada.
- Ausência de rig não reprova a entrada básica do Avatar Setup, mas bloqueia a classificação como corpo R15 final.

## Decisão

Não corrigir este arquivo com Smooth global, Merge by Distance ou Remesh automático. A quantidade e distribuição dos defeitos indicam reconstrução controlada com manifesto de componentes e comparação multiview. Qualquer saída deve receber novo SHA-256 e nova auditoria completa.
