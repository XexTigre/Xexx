# Agent Operating Contract

## Mandatory order

1. Read `.specify/memory/constitution.md`.
2. Read `sources/source_registry.yaml` and reject stale mandatory sources.
3. Create or update a measurable specification.
4. Lock the contract and referenced inputs by SHA-256.
5. Build without weakening thresholds.
6. Validate the exported artifact, not only the editor state.
7. Record claims and evidence separately.
8. Run an independent review.
9. Compute the release decision with `src/fail_closed_gate.py`.

## Truthfulness rules

- Never invent measurements, hashes, screenshots, Studio results or validator output.
- Never treat tool completion as proof of correctness.
- Never infer `PASS` from missing findings.
- Missing evidence means `BLOCKED`.
- Contradictory evidence means `REJECTED` until resolved.
- A claim may be `VERIFIED` only when every referenced evidence file exists and its digest matches.
- Never say an asset passed Roblox Studio unless a Studio report identifies the exact artifact SHA-256.
- Never silently change a contract after generation begins.
- Never let the generator approve its own critical output.

## Learning

New knowledge is a candidate until a PR includes: source, reproduction, failing test, correction, passing regression test and reviewer approval. The agent must not write directly to trusted memory.
