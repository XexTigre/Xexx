# Agent Operating Contract

## Mandatory order

1. Read `.specify/memory/constitution.md`.
2. Read `sources/source_registry.yaml` and reject stale mandatory sources.
3. Read `knowledge/index.yaml` and `specs/CROSS_SPEC_MATRIX.md`.
4. Select exactly one primary `pipeline_id` before rotating, renaming, partitioning, rigging, caging, or validating the asset.
5. Select one `change_scope` and load `specs/MESH_PRESERVATION_AND_DEFORMATION_SPEC.md`, `policies/mesh_preservation_policy.yaml`, and `schemas/mesh_preservation_contract.schema.json`.
6. Load the pipeline spec, `policies/cross_spec_policy.yaml`, and `schemas/cross_asset_contract.schema.json`.
7. Create or update a measurable job specification.
8. Lock the contract, original artifact, baseline, edit mask, and referenced inputs by SHA-256.
9. Build without weakening thresholds and without overwriting the only original.
10. Validate the exported artifact, not only the editor state.
11. Compare baseline versus output and run all mandatory pose tests.
12. Record claims and evidence separately.
13. Run an independent review.
14. Compute the release decision with the fail-closed gates.

## Pipeline separation

- `avatar_setup_body_input` and `r15_final_body` are different stages and MUST NOT share one approval decision.
- Avatar Setup input faces `-Z`; final character body faces `+Z`, with `+Y` up.
- One or more meshes can be valid Avatar Setup input; a final R15 body requires exactly 15 named render meshes.
- Avatar Setup output is a new artifact requiring a new hash, inventory, proof board, Studio result, preservation comparison, and release decision.
- Local geometry or visual checks cannot stand in for Studio/UGC validation.

## Preservation and non-deformation rules

- Treat the source artifact as immutable. Work on a copy.
- Never expand `change_scope` silently. A scope change requires a new contract and baseline.
- `texture_only` must preserve geometry, topology, vertex order, UV, rig, weights, cages, attachments, transforms, shape keys, and FACS.
- `geometry_local_fix` may move only vertices inside the hashed edit mask; unapproved moved vertices must be zero.
- `rig_weight_fix` must preserve the rest-pose geometry, topology, UV, cages, attachments, and armature rest pose.
- `cage_fix` must preserve Roblox cage vertex count, topology, vertex order, and UV.
- Do not apply Decimate, Remesh, Weld, Merge by Distance, Boolean, global Smooth, applied Shrinkwrap, Surface Deform, Mesh Deform, or Subdivision unless the exact operation is authorized by the locked contract.
- Do not apply transforms blindly to an already rigged or animated armature. Blender recommends applying armature transforms before rigging and animation; later changes require a controlled copy and equivalence proof.
- Automatic weights, weight transfer, Preserve Volume, and Corrective Smooth are not proof of correct deformation. They require normalization, influence limits, protected-region comparison, and pose tests.
- Corrective Smooth must be local, follow Armature, stay within factor 0–1, and prove that it did not flatten the face, neck, caps, or silhouette.
- Never alter outer-cage topology or UVs. Roblox warns that adding/removing cage vertices or changing cage UVs can break import and layered clothing fit.
- Reopen and measure the exported GLB/FBX. The Blender viewport is not the final artifact.

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
