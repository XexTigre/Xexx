# Review — body and facial rig V1

## Artifact

- output: `RBX_ANIME_DOLL_RIGGED_FACE_BONES_V1.glb`
- SHA-256: `68bf4a9b71ee8861536d254d78e7d51e2bc652f1828601fa1edd45ef47d07fc9`
- source SHA-256: `b551a526e6d613132fb6b5dd2ae3a6c0cf4ff44a980a31c00906fcadc976a142`

## Confirmed local results

- pre-existing positions, normals, UVs, indices and embedded image bytes preserved;
- 49 joints: 17 body + 32 face;
- DynamicHead/RootFaceJoint present;
- 8 eyelid joints and separate eyes, jaw, lips and tongue;
- max 4 influences; zero Root weights; normalized sums;
- rest-pose maximum vertex delta: `5.266404692189068e-07` stud;
- GLB reopened locally with 20 geometry objects and 9,864 triangles;
- external face proof: 50 angles;
- internal face proof: 50 angles;
- 8 deformation pose tests;
- local contract gate: `RIGGED_LOCAL_REVIEWED`;
- adversarial gate tests: 5 passed.

## Truth boundary

This is a locally reviewed skinned glTF candidate. FACS mapping is not implemented. Khronos Validator, locked Blender reimport, Roblox Studio and UGC remain `NOT_RUN`. It is not a final Marketplace dynamic head or R15 release.
