#!/usr/bin/env python3
"""Fail-closed release gate. It never trusts a declared PASS."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEX64 = set("0123456789abcdef")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def valid_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def check_file(base: Path, record: dict[str, Any], path_key: str, hash_key: str, reasons: list[str]) -> bool:
    path_value = record.get(path_key)
    expected = record.get(hash_key)
    if not isinstance(path_value, str) or not valid_digest(expected):
        reasons.append(f"missing identity fields: {path_key}/{hash_key}")
        return False
    path = (base / path_value).resolve()
    if not path.is_file():
        reasons.append(f"missing evidence file: {path_value}")
        return False
    actual = sha256_file(path)
    if actual != expected:
        reasons.append(f"digest mismatch: {path_value}")
        return False
    return True


def decide(payload: dict[str, Any], base: Path) -> dict[str, Any]:
    blocked: list[str] = []
    rejected: list[str] = []

    artifact = payload.get("artifact", {})
    contract = payload.get("contract", {})
    artifact_ok = check_file(base, artifact, "path", "sha256", rejected)
    contract_ok = check_file(base, contract, "path", "sha256", rejected)

    artifact_hash = artifact.get("sha256", "")
    contract_hash = contract.get("sha256", "")
    generator_id = payload.get("generator_id")
    requirements = payload.get("mandatory_requirement_ids")
    claims = payload.get("claims")
    runs = payload.get("validation_runs")

    if not isinstance(generator_id, str) or not generator_id:
        blocked.append("generator identity missing")
    if not isinstance(requirements, list) or not requirements:
        blocked.append("mandatory requirements missing")
        requirements = []
    if not isinstance(claims, list):
        blocked.append("claims missing")
        claims = []
    if not isinstance(runs, list) or not runs:
        blocked.append("validation runs missing")
        runs = []

    verified: set[str] = set()
    failed: set[str] = set()

    for claim in claims:
        if not isinstance(claim, dict):
            rejected.append("malformed claim")
            continue
        requirement = claim.get("requirement_id")
        status = claim.get("status")
        if claim.get("artifact_sha256") != artifact_hash:
            rejected.append(f"claim artifact mismatch: {requirement}")
            continue
        evaluator = claim.get("evaluator_id")
        if evaluator == generator_id:
            rejected.append(f"self-certified claim: {requirement}")
            continue
        evidence = claim.get("evidence")
        if status == "VERIFIED":
            if not isinstance(evidence, list) or not evidence:
                rejected.append(f"verified claim without evidence: {requirement}")
                continue
            evidence_ok = True
            for item in evidence:
                if not isinstance(item, dict) or not check_file(base, item, "path", "sha256", rejected):
                    evidence_ok = False
            if evidence_ok and isinstance(requirement, str):
                verified.add(requirement)
        elif status == "FAILED" and isinstance(requirement, str):
            failed.add(requirement)
        elif status in {"UNKNOWN", "NOT_RUN"}:
            blocked.append(f"requirement not verified: {requirement}")
        else:
            rejected.append(f"invalid claim status: {requirement}")

    independently_covered: set[str] = set()
    for run in runs:
        if not isinstance(run, dict):
            rejected.append("malformed validation run")
            continue
        validator = run.get("validator", {})
        validator_id = validator.get("id") if isinstance(validator, dict) else None
        if validator_id == generator_id:
            rejected.append("generator used as validator")
        if run.get("artifact_sha256") != artifact_hash:
            rejected.append("validation run artifact mismatch")
        if not check_file(base, run, "report_path", "report_sha256", rejected):
            continue
        result = run.get("result")
        if result == "FAIL":
            rejected.append(f"validator failed: {validator_id}")
        elif result in {"ERROR", "NOT_RUN"}:
            blocked.append(f"validator unavailable: {validator_id}")
        elif result == "PASS":
            covered = run.get("covered_requirement_ids")
            if not isinstance(covered, list) or not covered:
                rejected.append(f"PASS without requirement coverage: {validator_id}")
            else:
                independently_covered.update(x for x in covered if isinstance(x, str))
        else:
            rejected.append(f"invalid validation result: {validator_id}")

    if payload.get("studio_required") is True:
        studio = payload.get("studio_report")
        if not isinstance(studio, dict):
            blocked.append("Roblox Studio report missing")
        else:
            if studio.get("artifact_sha256") != artifact_hash:
                rejected.append("Studio report artifact mismatch")
            if studio.get("result") == "FAIL":
                rejected.append("Roblox Studio test failed")
            elif studio.get("result") != "PASS":
                blocked.append("Roblox Studio test not passed")
            check_file(base, studio, "report_path", "report_sha256", rejected)

    mandatory = set(x for x in requirements if isinstance(x, str))
    missing_claims = mandatory - verified - failed
    missing_independent = mandatory - independently_covered
    if failed:
        rejected.append("mandatory requirements failed: " + ", ".join(sorted(failed)))
    if missing_claims:
        blocked.append("mandatory claims missing: " + ", ".join(sorted(missing_claims)))
    if missing_independent:
        blocked.append("independent coverage missing: " + ", ".join(sorted(missing_independent)))

    if rejected or not artifact_ok or not contract_ok:
        decision = "REJECTED"
        reasons = sorted(set(rejected + blocked))
    elif blocked:
        decision = "BLOCKED"
        reasons = sorted(set(blocked))
    else:
        decision = "APPROVED"
        reasons = ["all mandatory requirements independently verified"]

    inputs = {
        "artifact": artifact_hash,
        "contract": contract_hash,
        "payload": canonical_sha256({k: v for k, v in payload.items() if k != "declared_decision"}),
    }
    result = {
        "decision_id": "release-" + inputs["payload"][:16],
        "artifact_sha256": artifact_hash,
        "contract_sha256": contract_hash,
        "decision": decision,
        "reasons": reasons,
        "input_digests": inputs,
        "computed_by": "fail_closed_gate",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "manual_override": False,
    }
    result["decision_sha256"] = canonical_sha256(result)
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fail_closed_gate.py RELEASE_INPUT.json", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1]).resolve()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = decide(payload, input_path.parent)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["decision"] == "APPROVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
