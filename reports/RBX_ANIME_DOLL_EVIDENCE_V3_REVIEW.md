# Review — RBX Anime Doll Evidence V3

## Artifact

- `RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb`
- SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`

## Confirmed local measurements

- 9,864 triangles; margin 878 under the 10,742 input budget used by the Avatar Setup contract;
- 20 geometry nodes;
- identity node transforms;
- zero physical boundary edges after deterministic position consolidation;
- zero physical non-manifold edges;
- no degenerate triangles or duplicate-face groups;
- embedded JPEG byte-exact;
- 9,740 textured UV triangles;
- zero exact nonzero-area UV-overlap pairs;
- 62-view silhouette IoU minimum 0.995762;
- 12-view SSIM minimum 0.979928;
- symmetry p95 0.109395 stud, reported as an internal warning.

## Adversarial correction

The first UV raster counted shared borders as repeated coverage and generated a false warning. Exact polygon intersection was added; contacts with zero area are excluded. The raster result is now diagnostic only.

## Gate result

`CANDIDATE_LOCAL_REVIEWED`

The following remain `NOT_RUN`: official Khronos validator, Blender import/reopen in the locked runtime for this exact artifact, Avatar Setup, Roblox Studio playtest and UGC validation. Therefore `release_eligible=false`.

## Test suite

Eight adversarial cases cover raster false positives, exact overlap, incomplete view sets, evidence tampering, self-certification and false release approval.
