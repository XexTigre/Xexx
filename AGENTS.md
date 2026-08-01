# Agent Operating Contract

## Mandatory order

1. Read `.specify/memory/constitution.md`.
2. Read `sources/source_registry.yaml` and reject stale mandatory sources.
3. Read `knowledge/index.yaml` and `specs/CROSS_SPEC_MATRIX.md`.
4. Before any Blender execution, read `blender_env/environment.lock.json` and `knowledge/BLENDER_EXECUTION_ENVIRONMENT.md`; use only the pinned version and safe runner.
5. Select exactly one primary `pipeline_id` before rotating, renaming, partitioning, rigging, caging, or validating the asset.
6. Select one `change_scope` and load `specs/MESH_PRESERVATION_AND_DEFORMATION_SPEC.md`, `policies/mesh_preservation_policy.yaml`, and `schemas/mesh_preservation_contract.schema.json`.
7. Select one `requested_scope` and load `specs/SCOPED_REAUDIT_SPEC.md`, `policies/scoped_reaudit_policy.yaml`, `schemas/scoped_reaudit.schema.json`, and `src/scoped_reaudit_gate.py`.
8. For enhanced visual evidence, load `specs/ENHANCED_EVIDENCE_AND_VISUALIZATION_SPEC.md`, `schemas/enhanced_evidence_contract.schema.json`, and `src/enhanced_evidence_gate.py`.
9. For exponential visual review, load `specs/EXPONENTIAL_VISUAL_VALIDATION_SPEC.md`, `schemas/exponential_visual_contract.schema.json`, and `src/exponential_visual_gate.py`.
10. Load the pipeline spec, `policies/cross_spec_policy.yaml`, and `schemas/cross_asset_contract.schema.json`.
11. Create or update a measurable job specification.
12. Lock the contract, original artifact, baseline, edit mask, and referenced inputs by SHA-256.
13. Build without weakening thresholds and without overwriting the only original.
14. Validate the exported artifact, not only the editor state.
15. Compare baseline versus output and run all mandatory pose tests.
16. Record claims and evidence separately.
17. Run an independent review.
18. Compute the scoped audit and release decisions with the fail-closed gates.

## Blender environment rules

- Production automation uses Blender `4.5.12 LTS` until a reviewed migration changes `blender_env/environment.lock.json`.
- Downloads must be obtained from the official Blender release directory and verified against its SHA-256 manifest before extraction.
- Automated runs must use `--background --factory-startup --disable-autoexec --python-exit-code 1`.
- Never enable embedded Python execution for an uploaded or external `.blend` file.
- Unit System must be `None`, Rotation must be `Degrees`, and 1 Blender Unit is treated as 1 stud.
- Blender's native workspace remains `+Z` up; Studio contracts are evaluated as `+Y` up after import/export conversion.
- Use the generated workspace collections: immutable source, working copy, rig/cages/attachments, evidence, quarantine, and export.
- The environment report and workspace validation report are mandatory evidence for Blender-generated claims.
- A different Blender version produces a different environment identity and requires fresh regression tests.

## Enhanced evidence rules

- Generate the canonical 62-view set from the exact artifact: 12 yaws at five pitches plus the two poles.
- Hash every board, report and measurement and bind it to the artifact SHA-256.
- Measure both render-index topology and physical position-consolidated topology; never confuse attribute seams with holes.
- Use exact polygon intersection area for UV overlap. Raster multi-coverage is diagnostic only because shared borders can be counted repeatedly.
- Keep overlap, gutter, border clearance and bleed as separate checks.
- Label IoU, SSIM, color, symmetry and gutter thresholds as internal project policies, not official Roblox limits.
- Local evidence can produce only `CANDIDATE_LOCAL_REVIEWED` until official Khronos, locked Blender import/reopen, Avatar Setup, Studio and UGC gates pass for the exact artifact.

## Exponential visual rules

- Use the power-of-two spatial pyramid `1×1`, `2×2`, `4×4`, `8×8`; record the expected 85 cells per image and reject coverage totals that do not reconcile.
- Run scales `1×`, `2×`, `4×`, `8×` and display the worst cells instead of publishing only averages.
- Empty/empty silhouette cells are neutral matches; never convert them into false IoU failures.
- External body regions require canonical visibility evidence. Mouthbag, upper teeth, lower teeth and tongue may be occluded externally and therefore require named geometry plus an isolated, hash-bound internal proof board.
- Every render pass, crop, zoom, table and metric must identify the exact artifact SHA-256.
- SSIM and MS-SSIM are supporting metrics only. They never substitute for geometry, Khronos, Blender reopen, Avatar Setup, Studio or UGC checks.
- The generator cannot self-certify. The gate must independently reopen evidence files, recalculate hashes and recompute the decision.
- `LOCAL_EXPONENTIAL_REVIEWED` never means `READY_FOR_ROBLOX` and never sets `release_eligible=true`.

## Scoped audit rules

- Never use a generic `PASS`, `APPROVED`, `VALIDATED` or `READY_FOR_ROBLOX`. Always name the exact scope.
- A lower scope never approves a higher scope: parsing the GLB does not prove Khronos conformance; preservation does not prove Avatar Setup readiness; Avatar Setup input readiness does not prove a final R15 body; local checks do not prove Studio or Marketplace acceptance.
- Record absolute output defects separately from regressions. `new_boundary_edge_count=0` cannot clear pre-existing open boundaries.
- `mesh_object_count` and `connected_component_count` are different metrics. Avatar Setup readiness requires a complete semantic component manifest, not only a summary count.
- `doubleSided=true` is a rendering flag, not evidence that geometry is closed.
- Project thresholds such as 62 views, UV gutter and visual similarity must be labeled `project`; do not present them as official Roblox limits.
- `release_eligible=true` is allowed only for `ugc_marketplace` after exact-artifact Studio/UGC evidence.
- The output of Avatar Setup is always a new artifact with a new hash, inventory, audit and release decision.

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
- Contradictory evidence means `FAILED` or `REJECTED` until resolved.
- A claim may be verified only when every referenced evidence file exists and its digest matches.
- Never say an asset passed Roblox Studio unless a Studio report identifies the exact artifact SHA-256.
- Never silently change a contract after generation begins.
- Never let the generator approve its own critical output.
- Never label a project heuristic as an official Roblox requirement.

## Learning

New knowledge is a candidate until a PR includes: source, reproduction, failing test, correction, passing regression test and reviewer approval. The agent must not write directly to trusted memory.
