import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from visual_audit_gate import evaluate  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_document(tmp_path: Path):
    artifact = tmp_path / "asset.glb"
    artifact.write_bytes(b"valid-asset")
    evidence = tmp_path / "render.png"
    evidence.write_bytes(b"valid-evidence")
    views = [
        {"view_id": f"v{i}", "yaw_deg": (i * 30) % 360, "pitch_deg": 0, "roll_deg": 0, "evidence_ids": ["render"]}
        for i in range(12)
    ]
    metric = lambda value, threshold, comparison: {
        "value": value,
        "threshold": threshold,
        "comparison": comparison,
        "status": "PASS",
        "evidence_ids": ["render"],
        "source_class": "project_quality_policy",
    }
    return {
        "schema_version": "1.0.0",
        "asset": {
            "asset_id": "test",
            "artifact_path": "asset.glb",
            "sha256": digest(b"valid-asset"),
            "pipeline": "avatar_setup_input",
            "format": "glb",
            "triangles": 9000,
            "mesh_count": 1,
            "component_count": 8,
            "generator_id": "generator",
        },
        "reference": {
            "image_path": "render.png",
            "sha256": digest(b"valid-evidence"),
            "width_px": 1024,
            "height_px": 1024,
            "measurement_basis": "normalized_ratios",
            "intentional_asymmetry_masks": [],
        },
        "coordinate_contract": {
            "up_axis": "+Y",
            "origin": "ground_center",
            "asset_front_axis": "-Z",
            "required_front_axis": "-Z",
            "centered_on_y_axis": True,
        },
        "scale_contract": {
            "unit": "stud",
            "profile": "Classic",
            "bounds": {"x": 3.0, "y": 6.5, "z": 1.2},
            "node_transform_baked": True,
            "real_world_cm_is_annotation_only": True,
        },
        "geometry": {
            "watertight": True,
            "boundary_edge_count": 0,
            "non_manifold_edge_count": 0,
            "allowed_open_components": ["left_eye", "right_eye", "mouth_bag"],
            "pose": "A",
        },
        "render_protocol": {
            "mode": "minimum_12",
            "camera": "orthographic",
            "width_px": 1024,
            "height_px": 1024,
            "crop_margin_ratio": 0.03,
            "clipped_pixels": 0,
            "passes": ["beauty", "flat_albedo", "silhouette", "wireframe", "normal", "uv_checker", "seam_heatmap"],
            "views": views,
        },
        "uv_contract": {
            "texture_width_px": 2048,
            "texture_height_px": 2048,
            "overlap_area_ratio": 0.0,
            "island_min_gutter_px": 16.0,
            "texture_border_clearance_px": 16.0,
            "bleed_px": 8.0,
            "island_count": 8,
        },
        "pixel_metrics": {
            "silhouette_iou": metric(0.98, 0.97, ">="),
            "contour_chamfer_px": metric(1.0, 1.5, "<="),
            "ssim": metric(0.97, 0.95, ">="),
            "lpips": metric(0.05, 0.08, "<="),
            "delta_e_2000_p95": metric(3.0, 5.0, "<="),
            "seam_band_delta_e_2000_p95": metric(2.0, 3.0, "<="),
            "mirror_delta_e_2000_p95": metric(3.0, 4.0, "<="),
        },
        "evidence": [{
            "evidence_id": "render",
            "path": "render.png",
            "sha256": digest(b"valid-evidence"),
            "kind": "render",
            "tool": "test-renderer",
            "tool_version": "1",
            "command": "render",
            "artifact_sha256": digest(b"valid-asset"),
        }],
        "review": {
            "generator_id": "generator",
            "validator_id": "validator",
            "reviewer_id": "reviewer",
            "reviewed_at": "2026-08-01T00:00:00Z",
        },
        "decision": {
            "status": "APPROVED",
            "computed_by": "visual_audit_gate.py",
            "manual_override": False,
            "reason_codes": [],
            "decision_sha256": "0" * 64,
        },
    }


def test_valid_case_approves(tmp_path):
    assert evaluate(base_document(tmp_path), tmp_path)["status"] == "APPROVED"


def test_missing_metric_blocks(tmp_path):
    doc = base_document(tmp_path)
    doc["pixel_metrics"]["lpips"]["value"] = None
    doc["pixel_metrics"]["lpips"]["status"] = "NOT_RUN"
    result = evaluate(doc, tmp_path)
    assert result["status"] == "BLOCKED"
    assert "METRIC_UNAVAILABLE:lpips" in result["reason_codes"]


def test_self_certification_rejects(tmp_path):
    doc = base_document(tmp_path)
    doc["review"]["reviewer_id"] = "generator"
    assert evaluate(doc, tmp_path)["status"] == "REJECTED"


def test_zero_uv_margin_rejects(tmp_path):
    doc = base_document(tmp_path)
    doc["uv_contract"]["island_min_gutter_px"] = 0.5
    doc["uv_contract"]["texture_border_clearance_px"] = 0.0
    reasons = evaluate(doc, tmp_path)["reason_codes"]
    assert "UV_GUTTER_TOO_SMALL" in reasons
    assert "UV_BORDER_CLEARANCE_TOO_SMALL" in reasons


def test_wrong_avatar_setup_axis_rejects(tmp_path):
    doc = base_document(tmp_path)
    doc["coordinate_contract"]["asset_front_axis"] = "+Z"
    assert "ASSET_FRONT_AXIS_MISMATCH" in evaluate(doc, tmp_path)["reason_codes"]


def test_evidence_tampering_rejects(tmp_path):
    doc = base_document(tmp_path)
    (tmp_path / "render.png").write_bytes(b"tampered")
    assert evaluate(doc, tmp_path)["status"] == "REJECTED"
