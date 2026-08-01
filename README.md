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

## Cadeia de confiança

1. A solicitação e a spec definem requisitos obrigatórios e mensuráveis.
2. Entradas e contrato são bloqueados por SHA-256.
3. O gerador produz o ativo e seu manifesto.
4. Validadores independentes registram ferramenta, versão, comando, relatório e hashes.
5. Cada alegação referencia evidências reais.
6. `src/fail_closed_gate.py` recalcula a decisão; o agente não escolhe o resultado.
7. Roblox Studio permanece um gate separado quando exigido.
8. Conhecimento novo entra por PR com reprodução e teste de regressão.

## Estados permitidos

- `APPROVED`: todos os requisitos obrigatórios foram comprovados e cobertos independentemente.
- `REJECTED`: existe falha, adulteração, conflito ou falso PASS comprovado.
- `BLOCKED`: faltam dados, validadores, fontes ou evidências.

Não existe estado `PASS_WITHOUT_EVIDENCE`.

## Regras principais

- Log sem erro não prova sucesso.
- O GLB exportado deve ser auditado; o estado do Blender não basta.
- Todo relatório deve apontar o SHA-256 do artefato validado.
- Gerador e validador crítico não podem ter a mesma identidade.
- Evidência visual não substitui métricas geométricas.
- Validação local não substitui teste real no Roblox Studio.
- `UNKNOWN`, `NOT_RUN` e `SKIPPED` não podem virar `VERIFIED`.
- Decisões são calculadas e não aceitam override manual.

## Estrutura

```text
.specify/memory/constitution.md
AGENTS.md
docs/RESEARCH_BASIS.md
sources/source_registry.yaml
policies/truthfulness.yaml
schemas/claim.schema.json
schemas/validation_run.schema.json
schemas/release_decision.schema.json
src/fail_closed_gate.py
tests/test_fail_closed_gate.py
.github/workflows/validate.yml
```

## Executar

```bash
python -m pip install -e .[dev]
pytest -q
python src/fail_closed_gate.py path/to/release_input.json
```

## Limite honesto

Este repositório valida contratos, hashes, evidências e decisões. Ele não prova que um GLB específico foi aceito pelo Roblox Studio sem o GLB, o relatório real do Studio e as demais evidências obrigatórias.
