# Enhanced Evidence and Visualization Specification v1.8

## Objective

Increase evidence density without promoting local images or heuristics to Roblox approval. Every proof must identify the exact artifact SHA-256 and the scope it supports.

## Required layers

1. **Container and glTF structure** — GLB header/chunks, JSON, buffers, buffer views, accessors, references, embedded images and finite numeric values.
2. **Physical geometry** — position-consolidated boundary edges, non-manifold edges, degenerate triangles, duplicate faces, winding, volumes and per-node topology.
3. **Surface data** — normals, UV range, exact polygon overlap, texture-byte identity and UV checker.
4. **Visual identity** — 62 orthographic silhouette views, 12 beauty comparisons, multipass board, source/output difference, measurements and symmetry diagnostics.
5. **External gates** — official Khronos validation, Blender import/reopen, Avatar Setup, Studio playtest and UGC validation.

## Canonical 62-view set

- yaw: 0° through 330° in 30° steps;
- pitch: -60°, -30°, 0°, +30°, +60°;
- poles: +90° and -90°;
- total: 62 views.

All views must use the same artifact, orthographic projection, exposure, framing policy and deterministic camera convention.

## UV truth rule

Raster multi-coverage is not an exact overlap measurement because triangle borders and shared vertices may be counted multiple times. Approval must use polygon intersection area:

- shared border/vertex: area zero, not overlap;
- nonzero intersection above the locked tolerance: overlap;
- the raster map remains a diagnostic only.

Exact-overlap PASS is separate from gutter and border-clearance quality. An atlas can have zero overlap and still risk bleeding.

## Internal policies

IoU, SSIM, color difference, symmetry and gutter thresholds are versioned project policies, not official Roblox limits. The report must label them as internal.

## Fail-closed release rule

Local evidence may produce `CANDIDATE_LOCAL_REVIEWED`. `release_eligible=true` requires all of:

- official Khronos glTF Validator report;
- Blender import/reopen report in the locked environment;
- Avatar Setup output and report for the exact input hash;
- Roblox Studio playtest evidence;
- UGC validation evidence when publication is intended.

A screenshot never substitutes for one of these gates.

## Primary sources

- Roblox Avatar Setup requirements: https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- Roblox character-body specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
- Roblox Studio character testing: https://create.roblox.com/docs/art/characters/testing/studio
- Khronos glTF Validator: https://github.com/KhronosGroup/glTF-Validator
- Blender command-line arguments: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
