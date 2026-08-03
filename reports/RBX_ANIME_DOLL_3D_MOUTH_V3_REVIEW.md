# Review — RBX Anime Doll true 3D mouth V3

## Exact artifacts

- clean Avatar Setup input: `RBX_ANIME_DOLL_AVATAR_SETUP_3D_MOUTH_V3.glb`
- clean SHA-256: `3515fb360b134114cb6180f74eeecd61fcc0159cb61aeccd67bbfac48e20d299`
- rigged FACS17 local proof: `RBX_ANIME_DOLL_3D_MOUTH_RIGGED_FACS17_V3.glb`
- rigged SHA-256: `cb4003ee33704640a5e280a24c1d3c68ef7855a84e1feb27890a8d024b1f1fa3`

## Reproduced defect

The earlier white/gray mouth bars were duplicate procedural teeth/tongue primitives placed in front of the character's existing true 3D mouth components. The repair removes those duplicates, opens only the head-shell region behind the lips and adds a contained inward mouthbag.

## Confirmed local contract

- no 2D Decal mouth;
- no pre-existing visible cage in the clean input;
- 22 geometry nodes and 9,913 triangles;
- front `-Z`, up `+Y`, identity transforms;
- separate upper/lower lips, upper/lower teeth, tongue and mouthbag;
- rigged proof has 51 joints, one skin, DynamicHead/RootFaceJoint and neutral plus 17 FACS frames;
- pre-existing geometry attributes and embedded texture remain byte-exact between clean and rigged proof artifacts;
- neutral, JawDrop, Pucker and internal JawDrop are reviewed in 50 angles each;
- movement sequence is recorded from Blender-rendered frames;
- exact artifact is checked by the official Khronos glTF Validator and Blender 4.5.12 fail-closed gate.

## Decision

`LOCAL_MOUTH_V3_ALL_REQUESTED_PROOF_GATES_PASS` is a scoped local decision. It does not claim Avatar Setup, Roblox Studio, UGC or Marketplace acceptance.

## Platform boundary

A final dynamic head still requires the Roblox technical outer cage, landmarks, FACS mapping and exact-artifact platform validation. The clean input omits a pre-existing visible cage only so Avatar Setup can generate the appropriate technical result.
