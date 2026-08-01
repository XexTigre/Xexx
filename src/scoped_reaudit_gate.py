from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _has_evidence(document: dict[str, Any], evidence_type: str, subject: str) -> bool:
    return any(
        item["evidence_type"] == evidence_type and subject in item["subject_ids"]
        for item in document["evidence"]
    )


def evaluate(document: dict[str, Any], root: Path) -> dict[str, Any]:
    blocked: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []

    artifact = document["artifact"]
    artifact_path = root / artifact["path"]
    if not artifact_path.is_file():
        blocked.append("ARTIFACT_MISSING")
    elif sha256_file(artifact_path) != artifact["sha256"]:
        failed.append("ARTIFACT_HASH_MISMATCH")

    for item in document["evidence"]:
        path = root / item["path"]
        if not path.is_file():
            blocked.append(f"EVIDENCE_MISSING:{item['evidence_id']}")
            continue
        if sha256_file(path) != item["sha256"]:
            failed.append(f"EVIDENCE_HASH_MISMATCH:{item['evidence_id']}")
        if item["artifact_sha256"] != artifact["sha256"]:
            failed.append(f"EVIDENCE_WRONG_ARTIFACT:{item['evidence_id']}")

    identities = {document["review"]["generator_id"], document["review"]["validator_id"], document["review"]["reviewer_id"]}
    if len(identities) != 3:
        failed.append("SELF_CERTIFICATION")
    if document["decision"]["manual_override"]:
        failed.append("MANUAL_OVERRIDE_FORBIDDEN")

    m = document["measurements"]
    scope = document["requested_scope"]

    manifest = document["component_manifest"]
    allowed_open_classes = {"left_eye", "right_eye", "mouthbag", "upper_teeth", "lower_teeth", "tongue"}
    if len(manifest) != m["connected_component_count"]:
        failed.append("COMPONENT_MANIFEST_COUNT_MISMATCH")
    derived_unknown = sum(item["classification"] == "unknown" for item in manifest)
    derived_classified = len(manifest) - derived_unknown
    if derived_unknown != m["unknown_component_count"] or derived_classified != m["classified_component_count"]:
        failed.append("COMPONENT_MANIFEST_SUMMARY_MISMATCH")
    derived_unexpected_boundaries = 0
    for item in manifest:
        if item["allowed_open_boundary"] and item["classification"] not in allowed_open_classes:
            failed.append(f"INVALID_OPEN_BOUNDARY_EXCEPTION:{item['component_id']}")
        if item["boundary_edge_count"] > 0 and not item["allowed_open_boundary"]:
            derived_unexpected_boundaries += item["boundary_edge_count"]
    if derived_unexpected_boundaries != m["unexpected_boundary_edge_count"]:
        failed.append("UNEXPECTED_BOUNDARY_SUMMARY_MISMATCH")

    if m["material_double_sided"]:
        warnings.append("DOUBLE_SIDED_IS_NOT_WATERTIGHT_EVIDENCE")
    if m["uv_gutter_px_2048"] < 16.0:
        warnings.append("PROJECT_UV_GUTTER_BELOW_POLICY")
    if m["uv_border_clearance_px_2048"] < 16.0:
        warnings.append("PROJECT_UV_BORDER_CLEARANCE_BELOW_POLICY")
    if document["enforce_project_quality"]:
        if "PROJECT_UV_GUTTER_BELOW_POLICY" in warnings:
            failed.append("PROJECT_UV_GUTTER_FAILED")
        if "PROJECT_UV_BORDER_CLEARANCE_BELOW_POLICY" in warnings:
            failed.append("PROJECT_UV_BORDER_CLEARANCE_FAILED")

    if scope == "container_parse":
        if not m["container_parse_ok"]:
            failed.append("GLB_CONTAINER_PARSE_FAILED")
        if not _has_evidence(document, "mesh_audit_report", "container_parse"):
            blocked.append("CONTAINER_PARSE_EVIDENCE_MISSING")

    elif scope == "gltf_spec_validation":
        if m["khronos_validator_status"] == "NOT_RUN":
            blocked.append("KHRONOS_VALIDATOR_NOT_RUN")
        elif m["khronos_validator_status"] == "FAIL":
            failed.append("KHRONOS_GLTF_VALIDATION_FAILED")
        if not _has_evidence(document, "khronos_report", "gltf_spec_validation"):
            blocked.append("KHRONOS_REPORT_MISSING")

    elif scope == "preservation":
        if not _has_evidence(document, "preservation_report", "preservation"):
            blocked.append("PRESERVATION_REPORT_MISSING")
        if document.get("baseline_defects"):
            warnings.append("PRESERVATION_DOES_NOT_CLEAR_BASELINE_DEFECTS")

    elif scope == "avatar_setup_input_readiness":
        if m["mesh_object_count"] < 1:
            failed.append("NO_MESH_OBJECT")
        if m["triangle_count"] > 10742:
            failed.append("AVATAR_SETUP_TRIANGLE_BUDGET_EXCEEDED")
        if m["front_axis"] != "-Z":
            failed.append("AVATAR_SETUP_FRONT_AXIS_MISMATCH")
        if m["pose"] not in {"A", "T"}:
            failed.append("AVATAR_SETUP_POSE_NOT_A_OR_T")
        if not m["centered_on_y_axis"]:
            failed.append("AVATAR_SETUP_NOT_CENTERED_ON_Y")
        for field, code in (
            ("distinct_neck_status", "DISTINCT_NECK"),
            ("accessory_geometry_absent_status", "ACCESSORY_GEOMETRY_ABSENT"),
            ("head_components_status", "HEAD_COMPONENTS"),
        ):
            if m[field] == "FAIL":
                failed.append(f"AVATAR_SETUP_{code}_FAILED")
            elif m[field] == "BLOCKED":
                blocked.append(f"AVATAR_SETUP_{code}_UNVERIFIED")
        if not m["texture_present"]:
            failed.append("AVATAR_SETUP_TEXTURE_MISSING")
        if not _has_evidence(document, "mesh_audit_report", "component_manifest"):
            blocked.append("COMPONENT_MANIFEST_EVIDENCE_MISSING")
        for subject, field in (("pose", "pose"), ("distinct_neck", "distinct_neck_status"), ("accessory_geometry_absent", "accessory_geometry_absent_status"), ("head_components", "head_components_status")):
            value = m[field]
            if value == "PASS" or (field == "pose" and value in {"A", "T"}):
                if not _has_evidence(document, "visual_board", subject) and not _has_evidence(document, "mesh_audit_report", subject):
                    blocked.append(f"SEMANTIC_EVIDENCE_MISSING:{subject}")
        if m["classified_component_count"] != m["connected_component_count"] or m["unknown_component_count"] > 0:
            failed.append("UNCLASSIFIED_CONNECTED_COMPONENTS")
        if m["unexpected_boundary_edge_count"] > 0:
            failed.append("UNEXPECTED_OPEN_BOUNDARIES")
        if m["non_manifold_edge_count"] > 0:
            failed.append("NON_MANIFOLD_EDGES")
        if not m["transform_identity"]:
            warnings.append("AVATAR_SETUP_TRANSFORM_NOT_FROZEN_PROJECT_STRICT")
            if document["enforce_project_quality"]:
                failed.append("PROJECT_TRANSFORM_IDENTITY_FAILED")
        if not _has_evidence(document, "mesh_audit_report", "avatar_setup_input_readiness"):
            blocked.append("AVATAR_SETUP_AUDIT_REPORT_MISSING")

    elif scope == "r15_final_readiness":
        if m["body_part_mesh_count"] != 15:
            failed.append("R15_BODY_PART_COUNT_NOT_15")
        if m["front_axis"] != "+Z" or m["up_axis"] != "+Y":
            failed.append("R15_AXIS_MISMATCH")
        if not m["transform_identity"]:
            failed.append("R15_TRANSFORMS_NOT_FROZEN")
        if m["boundary_edge_count"] > 0:
            failed.append("R15_GEOMETRY_NOT_WATERTIGHT")
        if m["non_manifold_edge_count"] > 0:
            failed.append("R15_NON_MANIFOLD_EDGES")
        if not m["rig_present"]:
            failed.append("R15_RIG_MISSING")
        if m["outer_cage_count"] != 15:
            failed.append("R15_OUTER_CAGE_COUNT_NOT_15")
        if m["attachment_count"] != 19:
            failed.append("R15_ATTACHMENT_COUNT_NOT_19")
        if m["triangle_count"] > 10742:
            failed.append("R15_TRIANGLE_BUDGET_EXCEEDED")

    elif scope == "studio_playtest":
        if m["studio_import_status"] == "NOT_RUN" or m["studio_playtest_status"] == "NOT_RUN":
            blocked.append("STUDIO_TEST_NOT_RUN")
        if m["studio_import_status"] == "FAIL" or m["studio_playtest_status"] == "FAIL":
            failed.append("STUDIO_TEST_FAILED")
        if not _has_evidence(document, "studio_import", "studio_import"):
            blocked.append("STUDIO_IMPORT_EVIDENCE_MISSING")
        if not _has_evidence(document, "studio_playtest", "studio_playtest"):
            blocked.append("STUDIO_PLAYTEST_EVIDENCE_MISSING")

    elif scope == "ugc_marketplace":
        if m["ugc_validation_status"] == "NOT_RUN":
            blocked.append("UGC_VALIDATION_NOT_RUN")
        elif m["ugc_validation_status"] == "FAIL":
            failed.append("UGC_VALIDATION_FAILED")
        if not _has_evidence(document, "ugc_validation", "ugc_marketplace"):
            blocked.append("UGC_VALIDATION_EVIDENCE_MISSING")

    if failed:
        status = "FAILED"
        reasons = sorted(set(failed + blocked))
    elif blocked:
        status = "BLOCKED"
        reasons = sorted(set(blocked))
    else:
        status = "SATISFIED"
        reasons = []

    release_eligible = status == "SATISFIED" and scope == "ugc_marketplace"
    canonical = json.dumps({"artifact_sha256":artifact["sha256"],"scope":scope,"status":status,"reasons":reasons,"release_eligible":release_eligible},sort_keys=True,separators=(",", ":")).encode()
    return {"scope":scope,"status":status,"release_eligible":release_eligible,"reason_codes":reasons,"warnings":sorted(set(warnings)),"decision_sha256":hashlib.sha256(canonical).hexdigest()}


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("contract_json",type=Path)
    args=parser.parse_args()
    doc=json.loads(args.contract_json.read_text(encoding="utf-8"))
    result=evaluate(doc,args.contract_json.parent)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result["status"]=="SATISFIED" else 1

if __name__=="__main__":
    raise SystemExit(main())
