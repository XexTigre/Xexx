# V15 Face Visibility Failure

## Exact artifact

- File: `RBX_ANIME_DOLL_AVATAR_SETUP_FRONT_3D_MOUTH_SYMMETRIC_V15.glb`
- SHA-256: `75a2dd5c6403b5846264a1f5730444d530aa669e193028f69a9f2ba0026d9bdd`
- Screenshot SHA-256: `f3dc7adf5aa819062883c6fb05c78a4806aaa91f1ee404de34fa7a62aeb4d719`

## Confirmed cause

The exported `Head_Geo_Input` contains a second primitive using `MouthRepairSkin3D`.

- no `baseColorTexture`;
- opaque;
- `doubleSided=true`;
- projected width is 2.103 times the external lip width;
- spans the external mouth region;
- reaches essentially the same front depth as the lips;
- frontmost in 227 of 493 sampled external mouth rays (46.04%).

The `MouthBag_Component` is also frontmost in 17 of 493 rays (3.45%).

This means the lips can exist in the GLB and still not appear because a different primitive is physically in front of them. The gray appearance in Studio is consistent with the flat, untextured repair material; the depth occlusion itself is confirmed independently of color.

## Decision

`REJECTED`

The V15 GLB must not be delivered or used as an Avatar Setup candidate.
