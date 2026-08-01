import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fail_closed_gate import decide


def write_file(base: Path, name: str, content: bytes = b"ok") -> dict:
    path = base / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}


def valid_payload(tmp_path: Path) -> dict:
    artifact = write_file(tmp_path, "asset.glb", b"synthetic-glb")
    contract = write_file(tmp_path, "contract.json", b"locked-contract")
    evidence = write_file(tmp_path, "evidence/geometry.json", b"measured")
    report = write_file(tmp_path, "reports/validator.json", b"validator-pass")
    return {
        "artifact": artifact,
        "contract": contract,
        "generator_id": "generator-A",
        "mandatory_requirement_ids": ["geometry.manifold"],
        "claims": [{
            "requirement_id": "geometry.manifold",
            "status": "VERIFIED",
            "artifact_sha256": artifact["sha256"],
            "evaluator_id": "validator-B",
            "evidence": [evidence]
        }],
        "validation_runs": [{
            "artifact_sha256": artifact["sha256"],
            "validator": {"id": "validator-B", "role": "validator"},
            "result": "PASS",
            "covered_requirement_ids": ["geometry.manifold"],
            "report_path": report["path"],
            "report_sha256": report["sha256"]
        }],
        "studio_required": False
    }


def test_fully_evidenced_release_is_approved(tmp_path):
    result = decide(valid_payload(tmp_path), tmp_path)
    assert result["decision"] == "APPROVED"
    assert result["manual_override"] is False
    assert len(result["decision_sha256"]) == 64


def test_verified_without_evidence_is_rejected(tmp_path):
    payload = valid_payload(tmp_path)
    payload["claims"][0]["evidence"] = []
    result = decide(payload, tmp_path)
    assert result["decision"] == "REJECTED"


def test_generator_cannot_validate_own_output(tmp_path):
    payload = valid_payload(tmp_path)
    payload["validation_runs"][0]["validator"]["id"] = "generator-A"
    result = decide(payload, tmp_path)
    assert result["decision"] == "REJECTED"


def test_missing_validator_is_blocked(tmp_path):
    payload = valid_payload(tmp_path)
    payload["validation_runs"] = []
    result = decide(payload, tmp_path)
    assert result["decision"] == "BLOCKED"


def test_tampered_evidence_is_rejected(tmp_path):
    payload = valid_payload(tmp_path)
    (tmp_path / payload["claims"][0]["evidence"][0]["path"]).write_bytes(b"tampered")
    result = decide(payload, tmp_path)
    assert result["decision"] == "REJECTED"
