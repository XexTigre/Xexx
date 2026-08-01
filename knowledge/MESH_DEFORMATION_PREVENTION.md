# Conhecimento: prevenção de deformação e preservação de identidade

## Princípio central

Uma correção não é aprovada apenas porque o arquivo importa, anima ou parece melhor em uma vista. O resultado deve preservar a identidade visual, a silhueta, o volume, a topologia protegida, o UV, os cages, os attachments e a pose de repouso conforme o escopo autorizado.

A cópia de entrada é imutável. Toda execução começa registrando o SHA-256 do arquivo original e uma linha de base mensurável. O agente trabalha em uma cópia e nunca sobrescreve o único original.

## Contratos por tipo de alteração

### Textura apenas

Pode mudar material, imagem, cor e parâmetros PBR autorizados. Não pode mudar:

- posições de vértices;
- contagem ou ordem de vértices, arestas e faces;
- UV;
- rig, rest pose ou pesos;
- cages;
- attachments;
- shape keys e FACS;
- orientação, escala ou pivô.

### Correção geométrica local

Somente os vértices incluídos na máscara de edição podem mover. Por padrão, não pode haver alteração de topologia, ordem de vértices, UV, rig, weights, cages ou attachments.

### Correção de rig/pesos

Pode mudar grupos e pesos autorizados. A geometria da pose de repouso, topologia, UV, cages e attachments devem permanecer idênticos. O resultado só é aceito após testes de poses críticas.

### Correção de cage

Pode mover posições de vértices do cage quando autorizado, mas não pode adicionar/remover vértices nem alterar a topologia ou o UV do template Roblox. A malha renderizada não pode mudar.

### Reconstrução completa

Pode alterar a estrutura apenas quando o contrato declarar `full_rebuild`. Ainda assim, deve provar fidelidade à referência, compatibilidade Roblox e ausência de regressões.

## O que não é bom fazer

- Não aplicar Decimate, Remesh, Voxel Remesh, Weld, Merge by Distance, Boolean, Subdivision aplicada ou retopologia automática em um ativo preservado sem autorização explícita.
- Não aplicar Smooth global para "consertar" uma região; ele move vértices para a média dos vizinhos e pode apagar rosto, dedos, boca, pescoço e contornos.
- Não usar Corrective Smooth com fator fora de 0–1; valores fora da faixa esperada podem distorcer a malha.
- Não aplicar transformações em armature já rigada/animada de forma cega. Aplicar transformações em armatures deve ser planejado antes do rig; depois disso requer cópia, rest pose, rebind ou prova de equivalência.
- Não transferir pesos e considerar o resultado aprovado sem normalizar, limitar influências, procurar vértices sem peso e testar poses.
- Não espelhar pesos quando a malha e a rest pose não são perfeitamente simétricas no eixo X.
- Não transferir pesos entre formas muito diferentes; mapeamentos por proximidade podem atribuir influência ao lado ou membro errado.
- Não apagar ou adicionar vértices em outer cages Roblox e não alterar seus UVs.
- Não usar Shrinkwrap, Surface Deform ou Mesh Deform como correção final sem congelar a configuração, medir o delta e provar que regiões protegidas não mudaram.
- Não aceitar o log "rodou sem erro" como prova. O GLB/FBX exportado deve ser reaberto e medido.
- Não corrigir boca, olhos, nariz, pescoço ou junções por suavização ampla. Use máscara local, simetria controlada e comparação antes/depois.
- Não reduzir thresholds durante a execução para fazer o resultado passar.

## Boas práticas de rig e pesos

- No máximo 4 influências por vértice para corpo Roblox.
- Nenhuma influência no Root.
- Zero vértices deformáveis sem peso.
- Normalizar pesos e usar `Limit Total = 4`.
- Limpar pesos muito pequenos somente com `Keep Single` ou validação equivalente para não criar vértices sem influência.
- Bloquear grupos que não devem mudar.
- Usar simetria apenas em zonas declaradas simétricas.
- Testar cotovelos, ombros, quadris, joelhos, pescoço e agachamento.
- `Preserve Volume` pode reduzir colapso em rotações, mas muda o método de deformação e deve ser comparado em todas as poses críticas.
- Corrective Smooth deve vir depois do Armature, usar vertex group local, `Pin Boundaries` quando necessário e prova de que não houve perda de volume.

## Linha de base obrigatória

Antes de qualquer edição, registrar:

- SHA-256 do artefato;
- contagens de vértices, arestas, faces e triângulos;
- hash de topologia e ordem de vértices;
- hash das posições em rest pose;
- bounds, volume e centro;
- 12 ou 62 silhuetas canônicas;
- hash de UV e métricas de gutter/overlap;
- armature, hierarquia, rest pose e pesos;
- cages e attachments;
- materiais, texturas e seus hashes;
- shape keys/FACS quando aplicável.

## Provas mínimas de preservação

- Regiões não autorizadas: zero vértices movidos acima da tolerância.
- Escopo `texture_only`: hashes geométricos, UV, rig, cages e attachments idênticos.
- Escopo `rig_weight_fix`: hash de posições em rest pose idêntico.
- Escopo `cage_fix`: topologia, ordem e UV do cage idênticos.
- Poses obrigatórias executadas sem `NOT_RUN`.
- Evidências ligadas ao SHA-256 exato do arquivo de saída.
- Revisor independente do gerador.

## Fontes de autoridade

- Roblox Character Body Specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
- Roblox Character Bodies: https://create.roblox.com/docs/avatar/character-bodies
- Roblox Avatar Setup: https://create.roblox.com/docs/avatar-setup
- Blender Armature Modifier: https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html
- Blender Weight Paint Editing: https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/editing.html
- Blender Data Transfer Modifier: https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/data_transfer.html
- Blender Corrective Smooth: https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/corrective_smooth.html
- Blender Apply Transforms: https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/apply.html
