# Roblox 3D Contract Brain

Gerador e validador orientado por especificações para ativos Roblox 3D. O GitHub funciona como memória versionada do agente: regras, fontes, schemas, evidências, decisões e lições só mudam por commit e revisão.

## Objetivo

Impedir que um agente declare `PASS`, `APPROVED`, `VALIDATED` ou `READY_FOR_ROBLOX` sem provas verificáveis vinculadas ao arquivo exato.

## Fluxo Spec-Driven

```text
CONSTITUTION → SPEC → CLARIFY → PLAN → TASKS → BUILD
             → VALIDATE → INDEPENDENT REVIEW → RELEASE
```

Ausência de evidência produz `BLOCKED` ou `REJECTED`, nunca aprovação presumida.

## Entrada obrigatória do cérebro

O agente deve carregar primeiro:

```text
knowledge/index.yaml
specs/CROSS_SPEC_MATRIX.md
policies/cross_spec_policy.yaml
schemas/cross_asset_contract.schema.json
specs/MESH_PRESERVATION_AND_DEFORMATION_SPEC.md
policies/mesh_preservation_policy.yaml
schemas/mesh_preservation_contract.schema.json
```

A matriz escolhe um único pipeline antes de qualquer alteração:

- `avatar_setup_body_input`;
- `r15_final_body`;
- `dynamic_head`;
- `rigid_accessory`;
- `layered_accessory`.

Depois disso, o contrato escolhe um único escopo de alteração:

- `texture_only`;
- `geometry_local_fix`;
- `rig_weight_fix`;
- `cage_fix`;
- `full_rebuild`.

Isso impede misturar regras contraditórias, como frente `-Z` para entrada do Avatar Setup e frente `+Z` para corpo R15 final, ou tratar uma edição de textura como autorização para mover vértices.

## Cadeia de confiança

1. A solicitação e a spec definem requisitos obrigatórios e mensuráveis.
2. Entradas, baseline, máscara de edição e contrato são bloqueados por SHA-256.
3. O gerador trabalha em uma cópia e produz um novo artefato.
4. Validadores independentes registram ferramenta, versão, comando, relatório e hashes.
5. O sistema compara baseline × saída, incluindo pose de repouso, topologia, UV, rig, cages e attachments.
6. Cada alegação referencia evidências reais.
7. Os gates recalculam a decisão; o agente não escolhe o resultado.
8. Roblox Studio permanece um gate separado quando exigido.
9. Conhecimento novo entra por PR com reprodução e teste de regressão.

## Estados permitidos

- `APPROVED`: todos os requisitos obrigatórios foram comprovados e cobertos independentemente.
- `REJECTED`: existe falha, adulteração, conflito, deformação indevida ou falso PASS comprovado.
- `BLOCKED`: faltam dados, validadores, fontes, poses ou evidências.

Não existe estado `PASS_WITHOUT_EVIDENCE`.

## Regras principais

- Log sem erro não prova sucesso.
- O arquivo exportado deve ser reaberto e auditado; o estado do Blender não basta.
- Todo relatório deve apontar o SHA-256 do artefato validado.
- Gerador e validador crítico não podem ter a mesma identidade.
- Evidência visual não substitui métricas geométricas.
- Validação local não substitui teste real no Roblox Studio.
- `UNKNOWN`, `NOT_RUN` e `SKIPPED` não podem virar `VERIFIED`.
- Decisões são calculadas e não aceitam override manual.
- A saída do Avatar Setup é um novo artefato e precisa de novo hash e nova validação completa.
- A malha original é imutável; toda correção ocorre em uma cópia.

## Specs cruzadas

```text
specs/CROSS_SPEC_MATRIX.md
specs/AVATAR_SETUP_INPUT_SPEC.md
specs/R15_FINAL_BODY_SPEC.md
specs/DYNAMIC_HEAD_AND_CAGE_SPEC.md
specs/ACCESSORY_PIPELINES_SPEC.md
specs/EXPORT_STUDIO_RELEASE_SPEC.md
```

O schema `schemas/cross_asset_contract.schema.json` usa condições por pipeline para bloquear, entre outros casos:

- corpo R15 final orientado como entrada do Avatar Setup;
- corpo final sem 15 meshes, 15 outer cages ou 19 attachments;
- rig com mais de quatro influências ou influência no Root;
- cabeça dinâmica sem cage, três landmarks ou pelo menos 17 poses FACS;
- acessório rígido com skinning;
- acessório em camadas sem inner/outer cage;
- aprovação sem evidência Studio/UGC quando obrigatória.

## Preservação da malha e prevenção de deformação

O módulo transversal de preservação contém:

```text
knowledge/MESH_DEFORMATION_PREVENTION.md
specs/MESH_PRESERVATION_AND_DEFORMATION_SPEC.md
policies/mesh_preservation_policy.yaml
schemas/mesh_preservation_contract.schema.json
src/mesh_preservation_gate.py
tests/test_mesh_preservation_gate.py
```

Ele bloqueia:

- textura alterando geometria, UV, rig, cages ou attachments;
- correção local movendo vértices fora da máscara autorizada;
- rig/pesos alterando a forma da pose de repouso;
- cage com vértices adicionados/removidos ou UV modificado;
- Decimate, Remesh, Weld, Merge by Distance, Boolean ou Smooth global não autorizados;
- aplicação cega de transformações em armature já rigada;
- pesos automáticos ou transferidos sem normalização, limite de quatro influências e testes de pose;
- colapso de volume em ombros, cotovelos, quadris, joelhos e pescoço;
- autoaprovação e evidências ligadas ao arquivo errado.

Os thresholds de silhueta, volume e simetria são política interna versionada, não alegações de limites oficiais Roblox.

## Auditoria visual intensiva

O módulo `schemas/roblox_visual_audit.schema.json` obriga o agente a gerar e registrar uma prova visual determinística, com:

- conjunto canônico de 62 vistas;
- passes beauty, albedo plano, silhueta, wireframe, normal, UV checker e seam heatmap;
- escala medida em studs e perfil Roblox declarado;
- métricas por pixel: IoU, Chamfer, SSIM, LPIPS e CIEDE2000;
- hashes para cada render, máscara, mapa e relatório;
- revisão independente e decisão fail-closed.

A regra “sem margem visível” não remove o padding UV. A política exige gutter e bleed suficientes para impedir linhas e vazamento de cor.

## Executar

```bash
python -m pip install -e .[dev]
pytest -q
python src/fail_closed_gate.py path/to/release_input.json
python src/visual_audit_gate.py path/to/visual_audit.json
python src/mesh_preservation_gate.py path/to/mesh_preservation_contract.json
```

## Limite honesto

Este repositório valida contratos, hashes, evidências e decisões. Ele não prova que um GLB/FBX específico foi aceito pelo Roblox Studio sem o arquivo exato, o relatório real do Studio e as demais evidências obrigatórias.
