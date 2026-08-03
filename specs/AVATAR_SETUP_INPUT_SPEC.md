# Avatar Setup Body Input Spec v1.1

## Scope

Use only for an artifact that will be processed by Roblox Avatar Setup. It is not a final R15-body approval contract.

## Required geometry

- `pipeline_id` MUST be `avatar_setup_body_input`.
- The body MAY contain one or more meshes.
- Total triangle count MUST be at most 10,742, with safety headroom because Avatar Setup may add segmentation caps.
- The character MUST have a general humanoid arrangement: head, torso, two arms, and two legs.
- The body MUST be upright in A-pose or T-pose. I-pose is not a strict rejection by Roblox, but the project policy marks it `DEGRADED_INPUT` because Roblox warns of lower-quality output.
- Limbs MUST NOT obscure or overlap each other in the front view.
- The front MUST face `-Z`; up MUST be `+Y`.
- The body SHOULD be centered around the Y axis and SHOULD be symmetrical unless asymmetry is an explicit design requirement.
- The model MUST be watertight except for the eye and mouth openings/components allowed by the Avatar Setup specification.
- The neck MUST remain distinct from the shoulders and upper torso.
- Embedded accessories, hair, eyebrows, eyelashes, beards, or clothing MUST NOT be included in the body input.

## Required head structure

The input MUST contain five distinct connected components:

1. left eye/eyebag component;
2. right eye/eyebag component;
3. upper teeth;
4. lower teeth;
5. tongue.

Eyes, teeth, and tongue MUST NOT share vertices with the head or with one another where the official specification requires separation.

## Rig preservation modes

The job MUST declare one mode:

- `generate_all`: no trusted body rig is supplied;
- `preserve_standard_body_rig`: provided body rig follows the required Roblox hierarchy/names;
- `preserve_body_and_face_rig`: single-mesh body with compatible body rig, facial rig, and FACS data.

If the input rig does not satisfy Roblox hierarchy and naming requirements, the agent MUST expect Avatar Setup to replace it and MUST NOT claim rig preservation.

## Texture input

- At least one texture map SHOULD be included.
- Multiple input textures MAY be baked by Avatar Setup into a single map.
- PBR channels MUST be inventoried separately before processing because baking can change them.

## Preflight evidence

The preflight report MUST include:

- exact artifact hash;
- mesh/component count;
- triangle inventory;
- open-boundary classification separating permitted eye/mouth openings from other holes;
- five head-component connectivity proof;
- front/up axis proof;
- pose and limb-clearance renders;
- neck-separation measurement/render;
- accessory detector result;
- texture/material inventory.

## Exit condition

Preflight success means only `READY_FOR_AVATAR_SETUP_ATTEMPT`. It MUST NOT be converted into `READY_FOR_ROBLOX`.
