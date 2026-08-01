# Permanent lessons — exponential visual validation

1. More screenshots do not automatically mean more proof. Coverage must be enumerated, hashed and tied to the exact GLB.
2. A power-of-two pyramid exposes both whole-character drift and small local defects. Grids 1×1, 2×2, 4×4 and 8×8 produce 85 cells per image.
3. Empty silhouette cells in both images are a match, not an IoU failure.
4. Internal teeth and tongue can be invisible in exterior renders. Validate their existence and provide isolated internal views instead of forcing exterior visibility.
5. Render-index boundary edges can come from UV seams or split normals. Physical boundary checks require deterministic position consolidation and must remain separate.
6. Exact UV overlap requires polygon intersection area. Raster multicounting can falsely flag shared borders.
7. MS-SSIM and SSIM are supporting perceptual metrics, not Roblox acceptance tests.
8. Local visual success never promotes Khronos, Blender, Avatar Setup, Studio or UGC gates from `NOT_RUN` to `PASS`.
9. The worst spatial cells must be displayed, not hidden behind an average score.
10. Thresholds are frozen before execution and identified as internal project policy.

## Accepted regression case

Artifact SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`

- 344 actual view-pass renders;
- 248 multiscale silhouette evaluations;
- 48 multiscale appearance evaluations;
- 5,270 silhouette cells;
- 1,020 appearance cells;
- 7,170 total quantitative observations;
- zero physical boundary edges;
- zero physical non-manifold edges;
- zero exact UV-overlap pairs;
- byte-exact embedded texture;
- local decision `LOCAL_EXPONENTIAL_REVIEWED`;
- external platform gates `NOT_RUN`.
