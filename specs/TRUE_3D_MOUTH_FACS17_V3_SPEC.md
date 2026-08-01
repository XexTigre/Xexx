# True 3D Mouth and FACS17 Specification v3

## Scope

This specification creates a true three-dimensional mouth for an Avatar Setup body-input candidate while preserving every previously accepted datum outside the locked mouth edit region.

## Locked source

The build must record the source artifact SHA-256 and preserve, byte-for-byte where applicable:

- POSITION outside the authorized edit mask;
- NORMAL outside the authorized edit mask;
- TEXCOORD_0;
- triangle indices outside the authorized edit mask;
- embedded image bytes;
- dimensions, origin and input orientation.

## Required geometry

- upper lip and lower lip are true geometry;
- connected inward mouthbag behind the lip opening;
- separate upper teeth, lower teeth and tongue;
- no shared vertices between head, teeth and tongue;
- internal components remain behind the neutral lip plane;
- no 2D Decal object or material substitute;
- no duplicate procedural tooth/tongue primitives;
- no pre-existing visible cage in the clean Avatar Setup input;
- front axis `-Z`, up axis `+Y`, identity node transforms;
- triangle count must stay at or below the locked Avatar Setup input budget.

## Rig and facial motion proof

The local proof artifact requires:

- `DynamicHead` as RootFaceJoint under `Head`;
- maximum four influences per vertex;
- normalized weights;
- zero weight on `Root`;
- neutral plus at least 17 named FACS proof frames;
- neutral surface drift within the locked tolerance;
- JawDrop opens the lips while teeth and tongue stay inside the mouthbag;
- Pucker closes/protrudes the lips without exposing internal backsides;
- left/right corner poses remain independent;
- blink and eye-look tests do not move mouth components.

## Mandatory evidence

- 50 neutral mouth views;
- 50 JawDrop views;
- 50 Pucker views;
- 50 internal JawDrop views;
- all 18 neutral/FACS frames;
- Blender 4.5.12 import, reopen and round-trip GLB report;
- motion video generated from Blender-rendered frames;
- official Khronos glTF Validator JSON with zero errors;
- SHA-256 manifest binding every evidence file to the exact artifact.

## Fail-closed rules

Reject or block when:

- any required evidence is missing or belongs to another SHA-256;
- a duplicate internal component appears in front of the lips;
- a neutral render exposes teeth, tongue or mouthbag through closed lips;
- geometry, UV or texture changes occur outside the authorized edit mask;
- the validator reports any error;
- fewer than 50 views are present in any required angular set;
- the generator self-certifies the output;
- Avatar Setup, Studio or UGC is claimed without exact-artifact platform evidence.

## Platform boundary

The clean input may intentionally omit a pre-existing cage so Avatar Setup can generate it. A final Roblox dynamic head or Marketplace release still requires the technical outer cage, landmarks, mapping and platform validation defined by Roblox.
