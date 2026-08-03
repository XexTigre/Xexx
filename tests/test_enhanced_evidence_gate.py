from __future__ import annotations

import hashlib
from pathlib import Path

from src.enhanced_evidence_gate import CANONICAL_VIEWS, evaluate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def document(tmp_path: Path) -> dict:
    artifact = tmp_path / "asset.glb"
    board = tmp_path / "board.png"
    artifact.write_bytes(b"glb")
    board.write_bytes(b"png")
    artifact_hash = digest(artifact)
    views = [
        {"yaw": yaw, "pitch": pitch, "silhouette_iou": 1.0, "evidence_ids": ["board"]}
        for yaw, pitch in sorted(CANONICAL_VIEWS)
    ]
    return {
        "schema_version": "1.0.0",
        "artifact": {"path": artifact.name, "sha256": artifact_hash},
        "topology": {
            "physical_boundary_edges": 0,
            "physical_nonmanifold_edges": 0,
            "degenerate_triangles": 0,
            "duplicate_face_groups": 0,
        },
        "texture": {"embedded_image_byte_exact": True},
        "uv": {
            "uv_outside_0_1_count": 0,
            "exact_nonzero_overlap_pairs": 0,
            "exact_overlap_area": 0.0,
            "exact_overlap_tolerance_area": 1e-12,
            "raster_multi_coverage_ratio_including_shared_edges": 0.2,
        },
        "multiview": {
            "views": views,
            "summary": {"silhouette_iou_min": 1.0, "ssim_min": 1.0},
        },
        "internal_policy": {"silhouette_iou_min": 0.995, "ssim_min": 0.95},
        "external_gates": {
            "khronos_gltf_validator": "NOT_RUN",
            "blender_import_reopen": "NOT_RUN",
            "roblox_avatar_setup": "NOT_RUN",
            "roblox_studio_playtest": "NOT_RUN",
            "ugc_validation": "NOT_RUN",
        },
        "evidence": [{
            "evidence_id": "board",
            "path": board.name,
            "sha256": digest(board),
            "artifact_sha256": artifact_hash,
        }],
        "review": {"generator_id": "gen", "validator_id": "val", "reviewer_id": "rev"},
        "decision": {"release_eligible": False, "manual_override": False},
    }


def test_complete_local_evidence_is_candidate(tmp_path: Path) -> None:
    assert evaluate(document(tmp_path), tmp_path)["status"] == "CANDIDATE_LOCAL_REVIEWED"


def test_raster_shared_edges_are_not_exact_overlap(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["uv"]["raster_multi_coverage_ratio_including_shared_edges"] = 0.99
    assert evaluate(doc, tmp_path)["status"] == "CANDIDATE_LOCAL_REVIEWED"


def test_exact_uv_overlap_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["uv"]["exact_nonzero_overlap_pairs"] = 1
    assert "EXACT_UV_OVERLAP_PRESENT" in evaluate(doc, tmp_path)["reason_codes"]


def test_missing_view_blocks(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["multiview"]["views"].pop()
    result = evaluate(doc, tmp_path)
    assert result["status"] == "BLOCKED"
    assert "CANONICAL_62_VIEW_SET_INCOMPLETE" in result["reason_codes"]


def test_evidence_tampering_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    (tmp_path / "board.png").write_bytes(b"tampered")
    result = evaluate(doc, tmp_path)
    assert "EVIDENCE_HASH_MISMATCH:board" in result["reason_codes"]


def test_self_certification_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["review"]["reviewer_id"] = "gen"
    assert "SELF_CERTIFICATION" in evaluate(doc, tmp_path)["reason_codes"]


def test_false_release_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["decision"]["release_eligible"] = True
    assert any(x.startswith("FALSE_RELEASE_APPROVAL:") for x in evaluate(doc, tmp_path)["reason_codes"])


def test_release_requires_all_external_gates(tmp_path: Path) -> None:
    doc = document(tmp_path)
    for key in doc["external_gates"]:
        doc["external_gates"][key] = "PASS"
    doc["decision"]["release_eligible"] = True
    assert evaluate(doc, tmp_path)["status"] == "RELEASE_APPROVED"
