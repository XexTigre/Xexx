# True 3D mouth V3 — permanent lessons

## Root cause reproduced

The damaged Studio preview was not caused by a missing 2D decal. The source already contained usable three-dimensional upper/lower lips, upper/lower teeth and tongue. A prior repair added duplicate procedural tooth/tongue primitives in front of those components, producing the visible white/gray bars and an incorrect neutral mouth.

## Safe correction

1. Keep the accepted source geometry, UVs, normals, indices and embedded texture immutable by SHA-256.
2. Reuse the original true 3D lip, tooth and tongue components.
3. Remove only the proven duplicate procedural primitives.
4. Cut only the small head-shell region directly behind the lips to create a physical opening.
5. Add an inward closed mouthbag behind the lips.
6. Keep upper teeth, lower teeth and tongue separate, fully inside the mouthbag and without shared vertices.
7. Build rig and FACS as an additive layer; the neutral pose must not move the approved surface.
8. Prove neutral, JawDrop, Pucker and internal mouth geometry from multiple angles in the pinned Blender environment.

## No decal and no visible cage

- The mouth is modeled geometry, not a 2D Decal.
- The Avatar Setup input contains no pre-existing visible cage.
- A final Marketplace dynamic head still requires the technical outer cage and landmarks defined by Roblox. The phrase `no cage` must never be used to claim that a final dynamic head can omit this platform requirement.

## Truth scopes

`LOCAL_MOUTH_V3_ALL_REQUESTED_PROOF_GATES_PASS` proves only the exact local artifact, official Khronos glTF report and pinned Blender import/reopen/render checks. Avatar Setup, Studio playtest and UGC validation remain separate platform gates and cannot be inferred from images.

## Regression identity

- clean Avatar Setup input SHA-256: `3515fb360b134114cb6180f74eeecd61fcc0159cb61aeccd67bbfac48e20d299`
- rigged FACS17 local-proof SHA-256: `cb4003ee33704640a5e280a24c1d3c68ef7855a84e1feb27890a8d024b1f1fa3`
