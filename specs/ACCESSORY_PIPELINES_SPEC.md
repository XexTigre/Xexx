# Rigid and Layered Accessory Cross-Spec v1.1

## Shared rules

- The accessory category and body-scale target MUST be declared before size validation.
- The final exported render asset MUST be a single mesh.
- Maximum triangle count is 4,000.
- Geometry MUST be watertight, without exposed holes/backfaces.
- Marketplace textures MUST be <= 2048x2048.
- Material, transparency, vertex color, hierarchy, and extraneous-object checks MUST pass.
- The accessory MUST be tested on an official mannequin or equivalent Studio fitting workflow.

## Rigid accessory branch

- Skinning data MUST NOT be present.
- The correct attachment name/type MUST be selected for the category.
- Attachment placement and orientation MUST be validated in Studio/AFT.
- The bounding box MUST fit the current Roblox size table for the selected body scale and category.
- Shoulder and collar attachment semantics MUST not be treated as interchangeable.

## Layered accessory branch

- The render mesh MUST be rigged/skinned or have a validated automatic skin-transfer result.
- At least one correctly named attachment MUST exist.
- Both inner and outer cages MUST exist and match required naming.
- Cage template topology/UV compatibility MUST be preserved.
- Wrapping MUST be tested across declared body-scale mannequins and with at least one under-layer/over-layer combination.
- Render mesh/cage intersections, inverted cage faces, and extreme stretching MUST be measured.
- Maximum bounds are 8x8x8 studs for the common layered clothing categories, while eyebrow/eyelash bounds use their specific smaller limits.

## Bundling with Avatar Setup

When Avatar Setup requires a base body for fitting, the body is a mannequin dependency, not part of the released accessory artifact. Evidence MUST distinguish the accessory hash from the mannequin/base-body hash.
