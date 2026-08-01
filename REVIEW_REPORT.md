# Review report — v0.2.0

Review date: 2026-07-31

## Review 1 — architecture and schemas: PASS

- Constitution precedes implementation.
- SDD research is documented from primary/standard sources.
- Claims, validation runs and release decisions have separate schemas.
- Positive claims require artifact identity and evidence references.
- Decisions permit only APPROVED, REJECTED or BLOCKED.

## Review 2 — false-PASS resistance: PASS

Adversarial tests cover:

- VERIFIED claim without evidence → REJECTED;
- generator validating its own output → REJECTED;
- missing validation run → BLOCKED;
- altered evidence after measurement → REJECTED;
- fully evidenced synthetic case → APPROVED.

The release gate recalculates file hashes and does not trust a declared result.

## Review 3 — publication and CI: PASS

- CI parses JSON and YAML before tests.
- CI runs adversarial tests on push and pull request.
- CI rejects bootstrap/opaque payload directories and files over 1 MB.
- CODEOWNERS covers trust-critical files.
- Installation does not depend on automatic package discovery.

## Scope limitation

PASS applies to the contract brain and its test design. It is not evidence that any particular GLB, avatar, head or accessory passed Blender, Khronos validation or Roblox Studio.
