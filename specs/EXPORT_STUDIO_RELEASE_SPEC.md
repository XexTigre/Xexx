# Export, Artifact Integrity, Studio, and Release Spec v1.1

## Export target

- Rigged/skinned avatar production SHOULD use FBX for the full Studio import feature set unless a declared workflow specifically requires glTF/GLB.
- GLB/glTF artifacts MUST pass Khronos structural validation when used.
- Export settings, application version, plugin version, and command/preset MUST be recorded.

## Final-artifact audit

After every export, the pipeline MUST reopen and audit the exported file. It MUST NOT trust the in-memory DCC scene.

Required inventory:

- SHA-256 and byte size;
- parser/validator version;
- nodes, meshes, primitives, materials, images, skins, joints, animations;
- final triangle counts by suffix/group;
- transforms and bounds;
- UV ranges and overlaps;
- open/non-manifold/zero-area geometry;
- names and duplicate/conflicting names;
- cages, attachments, and rig hierarchy;
- external/missing resources.

## Studio gate

The exact artifact hash MUST be tied to:

- import timestamp and Studio version/channel;
- importer settings and selected rig scale;
- import warnings/errors;
- generated hierarchy inventory;
- Avatar Setup stage and settings, when used;
- playtest result;
- UGC validation result for Marketplace-targeted assets.

The UGC validation categories MUST be represented independently: schema, mesh geometry, texture/materials, rigging/skinning, cages, attachments, dynamic head, and security/moderation.

## Regression gate

Every accepted fix MUST add:

- failing fixture or machine-readable failure report;
- expected decision before fix;
- changed rule or implementation;
- expected decision after fix;
- artifact/evidence hashes;
- reviewer identity.

## Release decision

`APPROVED` is computed only when all mandatory checks for the declared pipeline are complete and bound to the same artifact. `BLOCKED` is used for missing tools/evidence. `REJECTED` is used for measured violations, hash conflicts, or self-certification.
