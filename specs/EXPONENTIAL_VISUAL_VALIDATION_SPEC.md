# Exponential Visual Validation Specification v2.0

## Objective

Increase visual evidence density using a power-of-two spatial pyramid while keeping local visual proof separate from Roblox platform approval.

## Coverage lattice

The mandatory local lattice is:

- 62 canonical orthographic views;
- four essential passes across all 62 views: beauty, silhouette, normal and semantic;
- eight extended passes across the 12 level azimuths: beauty, albedo, silhouette, normal, depth, semantic, UV checker and wireframe;
- scale factors `1, 2, 4, 8`;
- spatial grids `1×1, 2×2, 4×4, 8×8`.

The spatial cell count per image is `1 + 4 + 16 + 64 = 85`. Empty silhouette cells in both source and output are neutral and score 1.0; they must not create false failures.

## Artifact identity

Every metric, board and evidence item must reference the same artifact SHA-256. A source comparison artifact has its own independent SHA-256. Evidence from Avatar Setup output cannot approve its input or vice versa.

## Required local checks

1. GLB container and accessor integrity.
2. Triangle budget for the selected pipeline.
3. Physical topology after deterministic position consolidation.
4. Render-index boundaries reported separately from physical holes.
5. Finite normalized normals.
6. UV range and exact nonzero-area polygon overlap.
7. Embedded texture byte identity when preservation is claimed.
8. Power-of-two multiscale silhouette comparison.
9. Power-of-two multiscale appearance comparison.
10. Semantic visibility for external body regions.
11. Isolated evidence for internal mouth components that are naturally occluded.
12. Evidence hashes and independent decision recomputation.

## Internal visual metrics

MS-SSIM, SSIM, IoU, CIEDE2000 and spatial-pyramid thresholds are project policies. They are not official Roblox limits. The original SSIM and multiscale SSIM methods compare structural information at one or multiple image scales; they must be combined with geometry and platform gates rather than used alone.

## Semantic rule

External body regions must appear in at least one canonical azimuth. Mouthbag, upper teeth, lower teeth and tongue may be hidden by the face shell; they pass the semantic presence check only when:

- the named component exists;
- it contains triangles;
- an isolated internal proof board is present and hash-verified.

## Fail-closed decision

Local outcomes:

- `LOCAL_EXPONENTIAL_REVIEWED` — local structural and visual checks pass.
- `LOCAL_EXPONENTIAL_REVIEWED_WITH_WARNINGS` — mandatory local checks pass but an internal quality threshold warns.
- `REJECTED_LOCAL` — structural, hash, topology, texture or exact-UV failure.
- `BLOCKED` — evidence or required tools are missing.

`release_eligible=true` is allowed only when Khronos validation, locked Blender import/reopen, Avatar Setup, Roblox Studio playtest and UGC validation all pass for the exact artifact chain.

## External authority

- Roblox Avatar Setup input requirements.
- Roblox final character body specifications.
- Roblox Studio character testing.
- Khronos glTF Validator.
- Blender command-line and orthographic camera documentation.
