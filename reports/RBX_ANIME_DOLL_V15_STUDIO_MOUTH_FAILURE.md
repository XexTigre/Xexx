# V15 Studio Mouth Failure

Status: **REJECTED FOR STUDIO DELIVERY**

The user supplied a Studio screenshot showing the V15 candidate facing forward but with the mouth assembly transformed into a large gray plate outside the face, teeth exposed, and a visible head/neck separation artifact.

## Evidence boundary

The screenshot proves a Studio-side visual failure for the tested candidate, but it does not independently expose the imported file SHA-256. Therefore the exact-hash platform gate remains unverified while the candidate itself is blocked from further delivery.

## Most probable structural causes

The V15 GLB contains separate `UpperLip_Component`, `LowerLip_Component`, and `MouthBag_Component` meshes in addition to the required upper teeth, lower teeth, and tongue. Roblox Avatar Setup requires two eye components and three distinct internal mouthparts housed in a connected mouthbag. Roblox head guidance describes lip vertices as part of the head mesh and the mouthbag as being inside the head mesh. Detached lip meshes and a detached mouthbag create an ambiguous component inventory for auto-rigging, skinning, and facial caging.

## Required V16 correction

1. Merge upper and lower lip geometry into `Head_Geo` while preserving separate lip vertex loops for opening.
2. Integrate the mouthbag into the head geometry and keep it fully internal in neutral pose.
3. Keep only upper teeth, lower teeth, and tongue as distinct internal mouth components, with no shared vertices.
4. Ensure eye and mouth landmarks target the head surface rather than eyeballs or mouthbag.
5. Re-run Blender neutral, JawDrop, Pucker, round-trip, and 50-view proofs.
6. Reject the artifact if Studio exposes any internal component, detached lip surface, or head/neck gap.

## Official references

- https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- https://create.roblox.com/docs/art/characters/facial-animation/create-basic-heads
- https://create.roblox.com/docs/avatar/dynamic-heads/validate
- https://create.roblox.com/docs/avatar-setup
