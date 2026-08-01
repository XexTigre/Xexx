# Agent Operating Contract

## Mandatory order

1. Read `.specify/memory/constitution.md`.
2. Read `sources/source_registry.yaml` and reject stale mandatory sources.
3. Read `knowledge/index.yaml` and `specs/CROSS_SPEC_MATRIX.md`.
4. Select exactly one primary `pipeline_id` before rotating, renaming, partitioning, rigging, caging, or validating the asset.
5. Load the pipeline spec, `policies/cross_spec_policy.yaml`, and `schemas/cross_asset_contract.schema.json`.
6. Create or update a measurable job specification.
7. Lock the contract and referenced inputs by SHA-256.
8. Build without weakening thresholds.
9. Validate the exported artifact, not only the editor state.
10. Record claims and evidence separately.
11. Run an independent review.
12. Compute the release decision with the fail-closed gates.

## Pipeline separation

- `avatar_setup_body_input` and `r15_final_body` are different stages and MUST NOT share one approval decision.
- Avatar Setup input faces `-Z`; final character body faces `+Z`, with `+Y` up.
- One or more meshes can be valid Avatar Setup input; a final R15 body requires exactly 15 named render meshes.
- Avatar Setup output is a new artifact requiring a new hash, inventory, proof board, Studio result, and release decision.
- Local geometry or visual checks cannot stand in for Studio/UGC validation.

## Truthfulness rules

- Never invent measurements, hashes, screenshots, Studio results or validator output.
- Never treat tool completion as proof of correctness.
- Never infer `PASS` from missing findings.
- Missing evidence means `BLOCKED`.
- Contradictory evidence means `REJECTED` until resolved.
- A claim may be `VERIFIED` only when every referenced evidence file exists and its digest matches.
- Never say an asset passed Roblox Studio unless a Studio report identifies the exact artifact SHA-256.
- Never silently change a contract after generation begins.
- Never let the generator approve its own critical output.
- Never label a project heuristic as an official Roblox requirement.

## Learning

New knowledge is a candidate until a PR includes: source, reproduction, failing test, correction, passing regression test and reviewer approval. The agent must not write directly to trusted memory.
