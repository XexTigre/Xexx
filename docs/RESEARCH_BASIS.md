# Research basis

Reviewed on 2026-07-31.

## Spec-Driven Development

The workflow follows GitHub Spec Kit concepts: constitution, specification, clarification, implementation plan, tasks, analysis and implementation. The important adaptation for 3D assets is that the specification must contain measurable geometry, rig, material, texture, export and Studio gates before construction begins.

Official project: https://github.com/github/spec-kit

## Machine-readable contracts

JSON Schema Draft 2020-12 is used to reject malformed requests, claims, reports and decisions before semantic evaluation.

Official specification: https://json-schema.org/draft/2020-12

## Provenance

The provenance model is influenced by SLSA: identify the subject by digest, record builder identity, invocation, dependencies and timestamps, and verify provenance rather than trusting a filename.

Official specification: https://slsa.dev/spec/v1.2/provenance

## Canonical hashing

JSON used in locked contracts should be serialized deterministically before hashing. RFC 8785 provides a canonicalization scheme suitable for reproducible digests.

Official RFC: https://www.rfc-editor.org/rfc/rfc8785

## GitHub governance

CODEOWNERS, protected branches/rulesets, required status checks and pull-request review should protect constitutions, schemas, policies and accepted lessons.

Official documentation:
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

## Roblox validation boundaries

Roblox Avatar Setup can generate rigging, skinning, cages and facial data, but its output is a new artifact and must be re-exported, re-hashed and revalidated. Character bodies, dynamic heads and accessories have different requirements and therefore require separate contracts.

Official documentation:
- https://create.roblox.com/docs/avatar-setup/auto-setup-requirements
- https://create.roblox.com/docs/avatar/character-bodies/specifications
- https://create.roblox.com/docs/avatar/dynamic-heads/specifications
- https://create.roblox.com/docs/avatar/rigid-accessories/specifications

## GLB structural validation

The Khronos glTF Validator is appropriate for container and specification checks, but cannot prove Roblox-specific rigging, cage, attachment or Studio behavior.

Official validator: https://github.com/KhronosGroup/glTF-Validator

## Derived design decision

No single validator may issue the final approval. Structural GLB checks, Blender scene checks, contract checks, evidence checks and Roblox Studio checks are separate evidence producers. The release gate only combines their signed/digested results.
