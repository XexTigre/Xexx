# Mesh Preservation and Deformation Specification

## 1. Objetivo

Impedir que correções de rig, textura, cage, orientação, exportação ou geometria degradem a forma original. Esta spec é transversal a todos os pipelines Roblox e deve ser carregada junto da spec principal do ativo.

## 2. Ordem obrigatória

1. Definir `pipeline_id` e `change_scope`.
2. Congelar o contrato e o arquivo original por SHA-256.
3. Produzir baseline antes da edição.
4. Definir regiões protegidas e máscara de edição.
5. Trabalhar em cópia.
6. Exportar novo artefato.
7. Reabrir o artefato exportado.
8. Comparar baseline × saída.
9. Executar testes de pose e Roblox Studio quando aplicável.
10. Calcular a decisão fail-closed.

## 3. Escopos válidos

- `texture_only`
- `geometry_local_fix`
- `rig_weight_fix`
- `cage_fix`
- `full_rebuild`

O agente não pode promover o escopo durante a execução. Uma mudança de escopo exige novo contrato e novo baseline.

## 4. Locks por escopo

| Propriedade | texture_only | geometry_local_fix | rig_weight_fix | cage_fix | full_rebuild |
|---|---:|---:|---:|---:|---:|
| Topologia render | LOCK | LOCK por padrão | LOCK | LOCK | pode mudar |
| Ordem de vértices | LOCK | LOCK por padrão | LOCK | LOCK | pode mudar |
| Posição rest pose | LOCK | máscara local | LOCK | LOCK | pode mudar |
| UV render | LOCK | LOCK por padrão | LOCK | LOCK | pode mudar com prova |
| Rig/rest pose | LOCK | LOCK | pesos podem mudar | LOCK | pode mudar |
| Cage topologia/UV | LOCK | LOCK | LOCK | LOCK | padrão Roblox continua obrigatório |
| Attachments | LOCK | LOCK | LOCK | LOCK | pode mudar com prova |
| Materiais/texturas | pode mudar | LOCK salvo autorização | LOCK | LOCK | pode mudar |

## 5. Regras de geometria

- Regiões não autorizadas não podem mover acima de `1e-5` stud.
- Em correção local, `unapproved_moved_vertex_count` deve ser zero.
- Se `topology_change_authorized=false`, contagens e hashes de topologia e ordem de vértices devem permanecer idênticos.
- Sem novas arestas abertas, non-manifold ou self-intersections.
- A orientação e a escala devem continuar correspondendo ao pipeline selecionado.
- O pescoço, ombros, quadris, olhos, pálpebras, lábios e caps são zonas protegidas por padrão.

## 6. Regras de rig e pesos

- Máximo de 4 influências por vértice.
- Zero influências no Root.
- Zero vértices deformáveis sem peso.
- Erro máximo da soma normalizada: `1e-4`.
- Transferência de pesos exige registro do método, source hash, max distance e validação posterior.
- `Nearest Face Interpolated` é preferível para superfícies geometricamente correspondentes, mas não é garantia de correção.
- Mirror de pesos exige rest pose simétrica e correspondência topológica.
- Automatic weights são apenas ponto de partida; nunca constituem aprovação.

## 7. Modificadores

### Armature

- Ordem declarada e hash da configuração.
- `Preserve Volume` só pode ser ativado/desativado com comparação de poses.
- Não aplicar o modificador destrutivamente antes da validação do rig.
- Não aplicar transformações na armature após o binding sem autorização explícita, cópia de segurança e regressão completa de poses.

### Corrective Smooth

- Deve ficar após Armature.
- Restrito por vertex group local.
- Fator entre 0 e 1.
- `Pin Boundaries` quando a correção alcança caps, bordas ou junções.
- Bind obrigatório quando modificadores construtivos anteriores alteram a correspondência de vértices.
- Prova de volume e silhueta antes/depois.

### Modificadores destrutivos

Decimate, Remesh, Weld, Boolean, aplicada de Subdivision, Shrinkwrap aplicada, Surface Deform aplicada e Mesh Deform aplicada são proibidos nos escopos preservativos, salvo autorização nominal no contrato.

## 8. Poses canônicas mínimas

Para corpo R15 rigado:

- `rest`
- `a_pose`
- `t_pose`
- `left_elbow_90`
- `right_elbow_90`
- `left_arm_overhead`
- `right_arm_overhead`
- `left_hip_flexion_90`
- `right_hip_flexion_90`
- `left_knee_90`
- `right_knee_90`
- `squat`
- `neck_left_45`
- `neck_right_45`

Para o pipeline de cabeça dinâmica isolada:

- `blink_left`
- `blink_right`
- `mouth_open`
- `smile`
- `frown`

Quando uma cabeça dinâmica fizer parte de um corpo completo, aplicar os dois conjuntos em contratos vinculados ao mesmo artefato final.

Nenhuma pose obrigatória pode ficar `NOT_RUN`, `UNKNOWN` ou `SKIPPED` em uma decisão `APPROVED`.

## 9. Métricas internas de preservação

Estes limites são política do projeto, não limites oficiais Roblox:

- Silhouette IoU fora da máscara de edição: `>= 0.995`.
- Contour Chamfer p95 fora da máscara: `<= 1 px` em render 1024 px.
- Razão de volume da rest pose: `0.995–1.005` para escopos preservativos.
- Simetria em regiões declaradas simétricas: erro p95 `<= 0.002` stud.
- Colapso de volume articular nas poses: razão mínima `>= 0.90` em relação ao baseline aprovado.
- Interseções novas fora de contatos declarados: zero.

## 10. Decisão

- `BLOCKED`: falta ferramenta, baseline, pose, evidência ou arquivo.
- `REJECTED`: hash incompatível, modificação não autorizada, deformação acima do limite, falso PASS ou autoaprovação.
- `APPROVED`: todos os locks, poses, métricas e evidências passaram.
