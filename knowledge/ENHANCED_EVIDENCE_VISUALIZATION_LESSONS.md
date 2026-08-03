# Permanent lessons — enhanced evidence and visualizations

## Evidence is scoped

- A parser PASS does not prove official glTF conformance.
- Watertight geometry does not prove Avatar Setup success.
- A 62-view board does not prove rigging, caging, attachments or Studio behavior.
- Pixel similarity does not prove Marketplace acceptance.

## Two topology views are required

Render-index topology retains duplicated vertices caused by UV seams, split normals and material boundaries. Physical topology consolidates deterministic equal positions before measuring holes. Reports must show both and must not call every render-index boundary a physical hole.

## Exact UV overlap must be geometric

A previous raster heatmap counted shared triangle borders as repeated coverage and produced a false overlap warning. The corrected method performs exact polygon intersections and ignores zero-area contacts. The accepted regression case has 9,740 textured UV triangles, zero nonzero-area overlap pairs and exact overlap ratio zero.

## Zero overlap is not enough

Gutter, texture-border clearance and bleed remain separate quality checks. They prevent mipmap/filtering artifacts but are internal quality policies unless an official platform source states otherwise.

## Artifact identity

Every board, JSON report and measurement must reference the same artifact SHA-256. Evidence from one GLB cannot approve a different GLB, including Avatar Setup output derived from it.

## Accepted local case

`RBX_ANIME_DOLL_AVATAR_SETUP_SAFE_REPAIR_V2.glb`

- SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`;
- triangles: 9,864 / 10,742;
- physical boundary edges: 0;
- physical non-manifold edges: 0;
- texture byte-exact: PASS;
- exact UV overlap pairs: 0;
- 62-view silhouette IoU minimum: 0.995762;
- 12-view SSIM minimum: 0.979928;
- symmetry p95: 0.109395 stud, retained as an internal warning;
- Khronos, Avatar Setup, Studio and UGC: NOT_RUN.

Decision: `CANDIDATE_LOCAL_REVIEWED`, never `READY_FOR_ROBLOX`.
