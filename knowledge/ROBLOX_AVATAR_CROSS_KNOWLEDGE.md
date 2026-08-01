# Roblox Avatar Contract Brain — Crossed Knowledge v1.1

## Durable lessons

1. **Stage before shape.** Determine whether the file is an Avatar Setup input or a final R15 body before rotating or renaming it.
2. **The axis conflict is intentional.** Avatar Setup body input faces `-Z`; final character-body specification faces `+Z`, with `+Y` up.
3. **Avatar Setup success is not release success.** Its output is a new artifact and requires a new hash and complete revalidation.
4. **One mesh can be valid input but invalid final output.** Avatar Setup accepts one or more meshes; a final body requires 15 named meshes.
5. **Watertight has stage-specific exceptions.** Avatar Setup allows the required eye/mouth structure; final separated body parts must be capped and watertight.
6. **Neck quality is both geometric and procedural.** A distinct neck is required for Avatar Setup; final head/torso partitioning, caps, weights, and cage continuity must also pass.
7. **Cage topology is sacred.** Body outer cages and layered inner/outer cages must preserve Roblox template topology/UV identity; moving vertices is allowed, destructive re-topology is not.
8. **Visual evidence is necessary but insufficient.** A 62-view board detects silhouette/color/seams, but cannot prove rig, cage, attachment, or Studio compatibility.
9. **No-margin appearance needs UV margin.** Preventing visible seams requires island gutter, border clearance, and texture bleed rather than islands touching.
10. **The exported artifact is the truth.** Always reopen the GLB/FBX and count the final components, triangles, names, transforms, and resources.
11. **Studio is an independent validator.** Local scripts cannot claim Studio or UGC success.
12. **No evidence means blocked, not passed.** Missing tools, views, reports, hashes, or validators produce `BLOCKED`.

## Required retrieval order for agents

1. `specs/CROSS_SPEC_MATRIX.md`
2. the declared pipeline spec;
3. `specs/PIXEL_VISUAL_AUDIT_SPEC.md` when appearance is a criterion;
4. `policies/cross_spec_policy.yaml`;
5. `schemas/cross_asset_contract.schema.json`;
6. current official sources from the source registry;
7. prior accepted lessons and regressions.
