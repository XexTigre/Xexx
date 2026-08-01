# Cross-Spec Review Report

## Review 1 — coverage

Added explicit contracts for Avatar Setup input, final R15 body, dynamic head/cage, rigid/layered accessories, export/Studio release, and a cross-pipeline router.

## Review 2 — contradiction control

Resolved the highest-risk contradictions:

- Avatar Setup `-Z` versus final body `+Z`;
- one-or-more input meshes versus exactly 15 final meshes;
- optional input rig versus mandatory final rig;
- input watertight exceptions versus capped final body parts;
- generated components versus preserved components;
- local validation versus Studio/UGC evidence.

## Review 3 — anti-false-PASS

The schema uses conditional pipeline constraints, exact artifact hashes, separate evidence items, `manual_override: false`, and only three release states. Missing evidence is not approval.

## Honest limitation

These specifications and schemas have been structurally reviewed. They do not claim that a particular GLB/FBX passed Studio or UGC validation without exact-artifact Studio evidence.
