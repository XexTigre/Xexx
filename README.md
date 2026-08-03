# Roblox 3D Contract Brain

Gerador e validador orientado por especificações para ativos Roblox 3D. O GitHub funciona como memória versionada do agente: regras, fontes, schemas, evidências, decisões e lições só mudam por commit e revisão.

## Objetivo

Impedir que um agente declare `PASS`, `APPROVED`, `VALIDATED` ou `READY_FOR_ROBLOX` sem provas verificáveis vinculadas ao arquivo exato.

## Fluxo Spec-Driven

```text
CONSTITUTION → SPEC → CLARIFY → PLAN → TASKS → BUILD
             → VALIDATE → INDEPENDENT REVIEW → RELEASE
```

Ausência de evidência produz `BLOCKED`, `FAILED` ou `REJECTED`, nunca aprovação presumida.

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
specs/SCOPED_REAUDIT_SPEC.md
policies/scoped_reaudit_policy.yaml
schemas/scoped_reaudit.schema.json
```

A matriz escolhe um único pipeline antes de qualquer alteração:

- `avatar_setup_body_input`;
- `r15_final_body`;
- `dynamic_head`;
- `rigid_accessory`;
- `layered_accessory`.

Depois disso, o contrato escolhe um único escopo de alteração e um único escopo de auditoria. Isso impede misturar regras contraditórias ou promover uma prova parcial a aprovação global.

## Auditoria por escopo

Os escopos são independentes:

```text
container_parse
gltf_spec_validation
preservation
avatar_setup_input_readiness
r15_final_readiness
studio_playtest
ugc_marketplace
```

- `container_parse=SATISFIED` não prova conformidade glTF pelo Khronos Validator.
- `preservation=SATISFIED` não prova que o baseline era bom.
- `avatar_setup_input_readiness=SATISFIED` não prova um corpo R15 final.
- somente `ugc_marketplace=SATISFIED`, com evidência real do mesmo SHA-256, pode produzir `release_eligible=true`.
- defeitos absolutos e regressões são medidos separadamente.
- um mesh object pode conter muitos connected components; para Avatar Setup, o manifesto semântico completo é obrigatório.
- `doubleSided=true` nunca é evidência de watertightness.

Consulte `knowledge/AUDIT_TRUTH_SCOPE_LESSONS.md` e `src/scoped_reaudit_gate.py`.

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

## Regras principais

- Log sem erro não prova sucesso.
- O arquivo exportado deve ser reaberto e auditado; o estado do Blender não basta.
- Todo relatório deve apontar o SHA-256 do artefato validado.
- Gerador, validador crítico e revisor devem ser identidades distintas.
- Evidência visual não substitui métricas geométricas.
- Validação local não substitui teste real no Roblox Studio.
- `UNKNOWN`, `NOT_RUN` e `SKIPPED` não podem virar aprovação.
- Decisões são calculadas e não aceitam override manual.
- A saída do Avatar Setup é um novo artefato e precisa de novo hash e nova validação completa.
- A malha original é imutável; toda correção ocorre em uma cópia.
- Heurísticas do projeto não podem ser apresentadas como requisitos oficiais Roblox.

## Preservação da malha e prevenção de deformação

O módulo transversal de preservação bloqueia alterações não autorizadas em geometria, topologia, UV, rig, weights, cages e attachments; operações destrutivas; aplicação cega de transformações; pesos não normalizados; colapso de volume; autoaprovação; e evidências ligadas ao arquivo errado.

Os thresholds de silhueta, volume, simetria, 62 vistas e padding UV são políticas internas versionadas, não alegações de limites oficiais Roblox.

## Executar

```bash
python -m pip install -e .[dev]
pytest -q
python src/fail_closed_gate.py path/to/release_input.json
python src/visual_audit_gate.py path/to/visual_audit.json
python src/mesh_preservation_gate.py path/to/mesh_preservation_contract.json
python src/scoped_reaudit_gate.py path/to/scoped_reaudit.json
```

## Limite honesto

Este repositório valida contratos, hashes, evidências e decisões. Ele não prova que um GLB/FBX específico foi aceito pelo Roblox Studio sem o arquivo exato, o relatório real do Studio e as demais evidências obrigatórias.
