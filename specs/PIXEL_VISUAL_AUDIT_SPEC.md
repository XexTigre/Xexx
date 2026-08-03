# Pixel-Intensive Visual Audit Spec for Roblox 3D

## 1. Purpose

This specification teaches an agent to produce proof boards like a multiview technical sheet while refusing to approve an asset from appearance alone. The proof board is an evidence artifact; it is not the validator itself.

## 2. Units and coordinate systems

- All export and validation dimensions use **Roblox studs**.
- Centimeters may appear only as explanatory annotations derived from normalized proportions. Never use `1 stud = 1 cm` as a strict Roblox rule.
- Up axis is `+Y` and the origin is the center between the soles on the ground plane.
- Avatar Setup input faces `-Z`.
- A final character body follows the character-body specification and faces `+Z`.
- The selected pipeline must therefore be recorded before the model is rotated or judged.

## 3. Scale contract

The audit stores the evaluated scene bounds in studs and checks them against one selected profile:

| Profile | X total | Y total | Z total |
|---|---:|---:|---:|
| Normal | 1.35–8.60 | 3.60–9.50 | 0.70–2.25 |
| Slender | 1.35–6.00 | 3.60–9.50 | 0.70–2.00 |
| Classic | 1.35–8.00 | 3.60–9.10 | 0.70–2.00 |

Node/object transforms must be baked. A visually correct size produced only by a non-identity node matrix is rejected by the strict contract because downstream tools may interpret it differently.

## 4. Intensive view protocol

### 4.1 Canonical 62-view set

- Yaw: `0°` through `330°`, step `30°`.
- Pitch bands: `-60°`, `-30°`, `0°`, `+30°`, `+60°`.
- Poles: `+90°` and `-90°`.
- Total: `12 × 5 + 2 = 62` views.

Each view uses the same orthographic scale, exposure, color management, background, crop policy, and image resolution. The camera may move around the fixed artifact; the artifact itself must not be reposed between views.

### 4.2 Required render passes

Every canonical view must have, directly or through a deterministic companion render:

1. beauty/shaded;
2. flat albedo without lighting;
3. binary silhouette;
4. wireframe;
5. normal map visualization;
6. UV checker;
7. seam heatmap;
8. texel-density map when texture fidelity is a release criterion.

### 4.3 Deterministic framing

“Without margin” must not mean clipping the object. The contract uses a fixed **3% frame margin** with ±0.5% tolerance, zero clipped pixels, and the same framing algorithm for every view. Arbitrary empty borders or manual crops are rejected.

## 5. Pixel-level measurements

Pixel metrics complement, but never replace, mesh and Studio validation.

- **Silhouette IoU:** detects proportion and missing-volume changes.
- **Contour Chamfer distance:** detects local shape drift along the outline.
- **SSIM:** detects structural changes after exact registration.
- **LPIPS:** detects perceptual changes not captured by raw pixel error.
- **CIEDE2000 ΔE:** detects color drift in aligned regions.
- **Seam-band ΔE:** samples a narrow band on both sides of every UV seam.
- **Mirror ΔE:** compares left and right regions after excluding declared intentional asymmetries.

Project thresholds are policy, not Roblox claims. The initial strict policy is:

| Metric | Gate |
|---|---:|
| Silhouette IoU | ≥ 0.97 |
| Contour Chamfer | ≤ 1.5 px at 1024 px |
| SSIM | ≥ 0.95 |
| LPIPS | ≤ 0.08 |
| Global ΔE2000 p95 | ≤ 5.0 |
| Seam-band ΔE2000 p95 | ≤ 3.0 |
| Mirror ΔE2000 p95 | ≤ 4.0 |

A metric may be tuned only through a versioned policy change and regression tests. An agent cannot loosen it inside one job.

## 6. UV and “no visible margin” rule

A visible gap on the model is prevented by **adding safe UV padding**, not by removing it.

At a 2048×2048 avatar texture, the strict project policy requires:

- zero unintended UV overlap area;
- at least 16 px between islands;
- at least 16 px from an island to the texture border;
- at least 8 px texture dilation/bleed beyond each island;
- seam-band color continuity within the ΔE gate.

The Blender Pack Islands operator explicitly supports a margin between UV islands. Therefore an atlas touching the texture border or leaving sub-pixel gutters is a failure even when the rendered front view looks acceptable.

## 7. Evidence binding

Every image, mask, heatmap, log, or Studio capture records:

- SHA-256 of the evidence file;
- SHA-256 of the exact 3D artifact;
- tool and version;
- command/settings;
- canonical view ID;
- generation timestamp.

Evidence for one GLB cannot approve another GLB. A modified texture, model, contract, or render invalidates the decision.

## 8. Fail-closed decision

- Missing file/tool/view/metric: `BLOCKED`.
- Failed threshold, wrong orientation, wrong hash, self-review, or invalid geometry: `REJECTED`.
- `APPROVED` is computed only when all mandatory checks and independent review pass.
- A screenshot saying “success” is not evidence unless tied to the same artifact hash and accompanied by the full report.

## 9. Official and research basis

- Roblox character body specifications: https://create.roblox.com/docs/avatar/character-bodies/specifications
- Roblox Avatar Setup requirements: https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- Roblox texture specifications: https://create.roblox.com/docs/art/modeling/texture-specifications
- Roblox Studio character testing: https://create.roblox.com/docs/art/characters/testing/studio
- Blender UV Pack Islands margin: https://docs.blender.org/manual/en/4.1/modeling/meshes/uv/editing.html
- SSIM: DOI 10.1109/TIP.2003.819861
- CIEDE2000 implementation paper: DOI 10.1002/col.20070
- LPIPS: DOI 10.1109/CVPR.2018.00068
