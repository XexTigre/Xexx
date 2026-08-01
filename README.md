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
```

A matriz escolhe um único pipeline antes de qualquer alteração:

- `avatar_setup_body_input`;
- `r15_final_body`;
- `dynamic_head`;
- `rigid_accessory`;
- `layered_accessory`.

Isso impede misturar regras contraditórias, como frente `-Z` para entrada do Avatar Setup e frente `+Z` para corpo R15 final.

## Cadeia de confiança

1. A solicitação e a spec definem requisitos obrigatórios e mensuráveis.
2. Entradas e contrato são bloqueados por SHA-256.
3. O gerador produz o ativo e seu manifesto.
4. Validadores independentes registram ferramenta, versão, comando, relatório e hashes.
5. Cada alegação referencia evidências reais.
6. Os gates recalculam a decisão; o agente não escolhe o resultado.
7. Roblox Studio permanece um gate separado quando exigido.
8. Conhecimento novo entra por PR com reprodução e teste de regressão.

## Estados permitidos

- `APPROVED`: todos os requisitos obrigatórios foram comprovados e cobertos independentemente.
- `REJECTED`: existe falha, adulteração, conflito ou falso PASS comprovado.
- `BLOCKED`: faltam dados, validadores, fontes ou evidências.

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
```

## Limite honesto

Este repositório valida contratos, hashes, evidências e decisões. Ele não prova que um GLB/FBX específico foi aceito pelo Roblox Studio sem o arquivo exato, o relatório real do Studio e as demais evidências obrigatórias.
