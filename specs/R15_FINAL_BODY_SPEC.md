# Final R15 Character Body Spec v1.1

## Scope

Use for a final Roblox character body after manual construction or after processing by Avatar Setup.

## Geometry and naming

The artifact MUST contain exactly these 15 render meshes:

`Head_Geo`, `UpperTorso_Geo`, `LowerTorso_Geo`, `LeftUpperArm_Geo`, `LeftLowerArm_Geo`, `LeftHand_Geo`, `RightUpperArm_Geo`, `RightLowerArm_Geo`, `RightHand_Geo`, `LeftUpperLeg_Geo`, `LeftLowerLeg_Geo`, `LeftFoot_Geo`, `RightUpperLeg_Geo`, `RightLowerLeg_Geo`, `RightFoot_Geo`.

Each separated limb/body part MUST be capped and watertight. Exposed holes, backfaces, zero-area triangles, and undeclared duplicate shells are release failures.

## Orientation, origin, and transformations

- Front: `+Z`.
- Up: `+Y`.
- Translation, rotation, and scale MUST be frozen/applied.
- Pivots MUST be at `0,0,0` as required by the body specification.
- `LowerTorso` and `Root` bone/joint positions MUST be `0,0,0`.
- Export pose SHOULD be I, A, or T pose, with the selected pose declared.

## Body scale

The contract MUST select `Normal`, `Slender`, or `Classic`. Total and part bounds MUST be compared with the current official Roblox table in studs. Centimeters MAY be displayed for human explanation but MUST NOT be treated as the export unit or as a fixed `stud-to-cm` rule.

## Triangle budgets

- DynamicHead: <= 4,000.
- Torso group: <= 1,750.
- LeftArm: <= 1,248.
- RightArm: <= 1,248.
- LeftLeg: <= 1,248.
- RightLeg: <= 1,248.
- Total: <= 10,742.

The audit MUST count the final exported triangles by body asset group, not only the Blender viewport total.

## Rig hierarchy and skinning

- The standard R15 hierarchy and names MUST be present, or a supported higher-fidelity hierarchy MUST be declared.
- Each vertex MUST have at most four bone/joint influences.
- No vertex may be influenced by `Root`.
- All weights MUST be finite, non-negative, and normalized within project tolerance.
- Required meshes MUST be bound to the intended armature.
- Higher-fidelity optional bones MUST follow Roblox names/hierarchy and require the corresponding Studio rig-description objects when applicable.

## Cages and attachments

- Exactly 15 body outer cages MUST exist and be named from the render mesh with `_OuterCage`.
- Cage template vertex count, topology identity, and UV identity MUST be preserved; no destructive vertex deletion or UV rewrite.
- Render geometry MUST remain inside the corresponding outer cage where required by validation.
- Exactly 19 official attachment points MUST be present with correct names, parent/body-part association, position, and orientation.
- `Root_Att` MUST be at `0,0,0`.

## Visibility and materials

- Body parts MUST be fully opaque.
- Each required body part must occupy the required significant portion of its bounding box in front/side/back validation views.
- Marketplace textures MUST be <= 2048x2048.
- Object material, transparency, and vertex-color defaults MUST satisfy Marketplace technical requirements.
- The body bundle MUST NOT contain extraneous scripts/parts or accessories prohibited by body policy.

## Release evidence

`APPROVED` requires all local gates plus:

- successful Studio import of the exact artifact;
- Avatar Setup/preview checks when applicable;
- locomotion/playtest evidence;
- clothing/cage fit evidence;
- UGC validation result for Marketplace target;
- current policy review.
