from __future__ import annotations

import hashlib
from pathlib import Path

from src.mesh_preservation_gate import REQUIRED_BODY_POSES, evaluate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def h(char: str) -> str:
    return char * 64


def snapshot() -> dict:
    return {
        "vertex_count": 100,
        "edge_count": 200,
        "face_count": 100,
        "triangle_count": 200,
        "topology_sha256": h("1"),
        "vertex_order_sha256": h("2"),
        "rest_position_sha256": h("3"),
        "uv_sha256": h("4"),
        "rig_sha256": h("5"),
        "cage_topology_sha256": h("6"),
        "cage_uv_sha256": h("7"),
        "attachment_sha256": h("8"),
    }


def document(tmp_path: Path, scope: str = "texture_only") -> dict:
    source = tmp_path / "source.glb"
    output = tmp_path / "output.glb"
    evidence = tmp_path / "proof.json"
    source.write_bytes(b"source")
    output.write_bytes(b"output")
    evidence.write_text("{}")
    output_hash = digest(output)
    poses = [
        {
            "pose_id": pose_id,
            "status": "PASS",
            "joint_volume_retention_ratio": 1.0,
            "new_self_intersection_count": 0,
            "evidence_ids": ["proof"],
        }
        for pose_id in sorted(REQUIRED_BODY_POSES)
    ]
    return {
        "contract_version": "1.2.0",
        "pipeline_id": "r15_final_body",
        "change_scope": scope,
        "artifact": {
            "source_path": source.name,
            "source_sha256": digest(source),
            "output_path": output.name,
            "output_sha256": output_hash,
        },
        "baseline": snapshot(),
        "output": snapshot(),
        "authorization": {
            "topology_change_authorized": False,
            "uv_change_authorized": False,
            "rest_shape_change_authorized": False,
            "authorized_modifier_ops": [],
            "edit_mask_sha256": None,
        },
        "deformation_controls": {
            "armature_transform_applied_after_binding": False,
            "corrective_smooth": {
                "used": False,
                "stack_after_armature": True,
                "factor": 0.0,
                "restricted_by_vertex_group": True,
                "pin_boundaries": True,
                "bind_required": False,
                "bind_completed": True,
            },
        },
        "geometry": {
            "unapproved_moved_vertex_count": 0,
            "max_unapproved_vertex_delta_stud": 0.0,
            "new_boundary_edge_count": 0,
            "new_non_manifold_edge_count": 0,
            "new_self_intersection_count": 0,
            "silhouette_iou_outside_mask": 1.0,
            "contour_chamfer_p95_px": 0.0,
            "rest_volume_ratio": 1.0,
            "symmetric_region_error_p95_stud": 0.0,
        },
        "rigging": {
            "max_influences_observed": 4,
            "root_influenced_vertex_count": 0,
            "unweighted_deform_vertex_count": 0,
            "normalized_weight_sum_error_max": 0.0,
            "armature_rest_pose_unchanged": True,
            "preserve_volume_changed": False,
            "weight_transfer_method": "none",
        },
        "cages": {
            "present": True,
            "topology_unchanged": True,
            "vertex_order_unchanged": True,
            "uv_unchanged": True,
        },
        "attachments": {"names_unchanged": True, "transforms_unchanged": True},
        "modifier_operations": [],
        "pose_tests": poses,
        "evidence": [{
            "evidence_id": "proof",
            "path": evidence.name,
            "sha256": digest(evidence),
            "artifact_sha256": output_hash,
            "tool": "test-validator",
            "tool_version": "1.0",
        }],
        "review": {"generator_id": "gen", "validator_id": "val", "reviewer_id": "rev"},
        "decision": {"status": "APPROVED", "manual_override": False},
    }


def test_complete_preservation_case_is_approved(tmp_path: Path) -> None:
    assert evaluate(document(tmp_path), tmp_path)["status"] == "APPROVED"


def test_texture_only_geometry_change_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["output"]["rest_position_sha256"] = h("9")
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "TEXTURE_ONLY_CHANGED_PROTECTED_DATA" in result["reason_codes"]


def test_global_smooth_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["modifier_operations"] = ["global_smooth"]
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "FORBIDDEN_OPERATION:global_smooth" in result["reason_codes"]


def test_missing_pose_blocks_approval(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["pose_tests"] = [p for p in doc["pose_tests"] if p["pose_id"] != "squat"]
    result = evaluate(doc, tmp_path)
    assert result["status"] == "BLOCKED"
    assert "POSE_MISSING:squat" in result["reason_codes"]


def test_joint_volume_collapse_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["pose_tests"][0]["joint_volume_retention_ratio"] = 0.5
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert any(code.startswith("JOINT_VOLUME_COLLAPSE:") for code in result["reason_codes"])


def test_self_certification_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["review"]["reviewer_id"] = doc["review"]["generator_id"]
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "SELF_CERTIFICATION" in result["reason_codes"]


def test_evidence_tampering_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    (tmp_path / "proof.json").write_text("tampered")
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "EVIDENCE_HASH_MISMATCH:proof" in result["reason_codes"]


def test_blind_armature_transform_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["deformation_controls"]["armature_transform_applied_after_binding"] = True
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "BLIND_ARMATURE_TRANSFORM_APPLY" in result["reason_codes"]


def test_non_local_corrective_smooth_is_rejected(tmp_path: Path) -> None:
    doc = document(tmp_path)
    doc["deformation_controls"]["corrective_smooth"].update({
        "used": True,
        "factor": 0.5,
        "stack_after_armature": True,
        "restricted_by_vertex_group": False,
    })
    result = evaluate(doc, tmp_path)
    assert result["status"] == "REJECTED"
    assert "CORRECTIVE_SMOOTH_NOT_LOCAL" in result["reason_codes"]
