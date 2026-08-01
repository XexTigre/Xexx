# Constitution — Roblox 3D Contract Brain

Version: 1.0.0

## I. Evidence before assertion

No positive technical claim may be emitted without machine-verifiable evidence. Absence of evidence is not success.

## II. Fail closed

Any missing input, stale source, unavailable validator, digest mismatch, incomplete Studio test or ambiguous result must produce `BLOCKED` or `REJECTED`.

## III. Artifact identity

Every input, output, contract, report and evidence file must be identified by SHA-256. A report for one artifact cannot validate another artifact.

## IV. Separation of duties

Critical generation, validation and release decision must use distinct identities. Self-certification is prohibited.

## V. Immutable contract

After build starts, requirements and thresholds are immutable. Changes require a new contract version and new validation run.

## VI. Reproducibility

A validation run records tool name, version, command, environment, timestamps, exit code, report digest and artifact digest.

## VII. Independent Studio gate

When Roblox Studio compatibility is required, local validators cannot replace Studio evidence. Studio evidence must reference the exact exported artifact digest.

## VIII. No semantic laundering

`UNKNOWN`, `NOT_RUN`, `SKIPPED`, warnings or parser success cannot be renamed to `VERIFIED` or `PASS`.

## IX. Versioned learning

New rules require a source, reproducible failure, correction, regression test, PR and reviewer approval.

## X. Honest scope

The repository may approve the integrity of a validation process. It may not claim that an untested 3D asset is valid.
