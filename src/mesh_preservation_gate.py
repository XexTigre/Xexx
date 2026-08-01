from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_BODY_POSES = {
    "rest", "a_pose", "t_pose", "left_elbow_90", "right_elbow_90",
    "left_arm_overhead", "right_arm_overhead", "left_hip_flexion_90",
    "right_hip_flexion_90", "left_knee_90", "right_knee_90", "squat",
    "neck_left_45", "neck_right_45",
}

FORBIDDEN_DEFAULT = {
    "decimate_apply", "remesh_apply", "voxel_remesh", "weld_apply",
    "merge_by_distance", "boolean_apply", "subdivision_apply", "shrinkwrap_apply",
    "surface_deform_apply", "mesh_deform_apply", "global_smooth",
    "cage_vertex_addition", "cage_vertex_deletion", "cage_uv_change",
    "blind_armature_transform_apply", "unvalidated_automatic_weights",
    "threshold_weakening",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same(snapshot_a: dict[str, Any], snapshot_b: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return all(snapshot_a[key] == snapshot_b[key] for key in keys)


def evaluate(document: dict[str, Any], root: Path) -> dict[str, Any]:
    blocked: list[str] = []
    rejected: list[str] = []

    artifact = document["artifact"]
    for label, path_key, hash_key in (
        ("SOURCE", "source_path", "source_sha256"),
        ("OUTPUT", "output_path", "output_sha256"),
    ):
        path = root / artifact[path_key]
        if not path.is_file():
            blocked.append(f"{label}_ARTIFACT_MISSING")
        elif sha256_file(path) != artifact[hash_key]:
            rejected.append(f"{label}_ARTIFACT_HASH_MISMATCH")

    evidence_ids: set[str] = set()
    for item in document["evidence"]:
        evidence_ids.add(item["evidence_id"])
        path = root / item["path"]
        if not path.is_file():
            blocked.append(f"EVIDENCE_MISSING:{item['evidence_id']}")
            continue
        if sha256_file(path) != item["sha256"]:
            rejected.append(f"EVIDENCE_HASH_MISMATCH:{item['evidence_id']}")
        if item["artifact_sha256"] != artifact["output_sha256"]:
            rejected.append(f"EVIDENCE_WRONG_ARTIFACT:{item['evidence_id']}")

    identities = {
        document["review"]["generator_id"],
        document["review"]["validator_id"],
        document["review"]["reviewer_id"],
    }
    if len(identities) != 3:
        rejected.append("SELF_CERTIFICATION")
    if document["decision"]["manual_override"]:
        rejected.append("MANUAL_OVERRIDE_FORBIDDEN")

    scope = document["change_scope"]
    baseline = document["baseline"]
    output = document["output"]
    auth = document["authorization"]

    topology_keys = ("vertex_count", "edge_count", "face_count", "topology_sha256", "vertex_order_sha256")
    render_lock_keys = topology_keys + ("rest_position_sha256", "uv_sha256")
    support_lock_keys = ("rig_sha256", "cage_topology_sha256", "cage_uv_sha256", "attachment_sha256")

    if scope == "texture_only":
        if not _same(baseline, output, render_lock_keys + support_lock_keys):
            rejected.append("TEXTURE_ONLY_CHANGED_PROTECTED_DATA")
    elif scope == "geometry_local_fix":
        if auth["edit_mask_sha256"] is None:
            blocked.append("EDIT_MASK_MISSING")
        if not auth["topology_change_authorized"] and not _same(baseline, output, topology_keys):
            rejected.append("UNAUTHORIZED_TOPOLOGY_CHANGE")
        if not auth["uv_change_authorized"] and baseline["uv_sha256"] != output["uv_sha256"]:
            rejected.append("UNAUTHORIZED_UV_CHANGE")
        if not _same(baseline, output, support_lock_keys):
            rejected.append("LOCAL_FIX_CHANGED_RIG_CAGE_OR_ATTACHMENTS")
    elif scope == "rig_weight_fix":
        keys = render_lock_keys + ("cage_topology_sha256", "cage_uv_sha256", "attachment_sha256")
        if not _same(baseline, output, keys):
            rejected.append("RIG_FIX_CHANGED_REST_GEOMETRY_UV_OR_CAGES")
        if not document["rigging"]["armature_rest_pose_unchanged"]:
            rejected.append("ARMATURE_REST_POSE_CHANGED")
    elif scope == "cage_fix":
        if not _same(baseline, output, render_lock_keys + ("rig_sha256", "attachment_sha256")):
            rejected.append("CAGE_FIX_CHANGED_RENDER_ASSET")
        cages = document["cages"]
        if not cages["topology_unchanged"] or not cages["vertex_order_unchanged"] or not cages["uv_unchanged"]:
            rejected.append("CAGE_TEMPLATE_CONTRACT_BROKEN")

    geometry = document["geometry"]
    if geometry["unapproved_moved_vertex_count"] > 0:
        rejected.append("UNAPPROVED_VERTICES_MOVED")
    if geometry["max_unapproved_vertex_delta_stud"] > 0.00001:
        rejected.append("UNAPPROVED_VERTEX_DELTA_TOO_LARGE")
    if geometry["new_boundary_edge_count"] > 0:
        rejected.append("NEW_BOUNDARY_EDGES")
    if geometry["new_non_manifold_edge_count"] > 0:
        rejected.append("NEW_NON_MANIFOLD_EDGES")
    if geometry["new_self_intersection_count"] > 0:
        rejected.append("NEW_SELF_INTERSECTIONS")
    if scope != "full_rebuild":
        if geometry["silhouette_iou_outside_mask"] < 0.995:
            rejected.append("SILHOUETTE_DRIFT")
        if geometry["contour_chamfer_p95_px"] > 1.0:
            rejected.append("CONTOUR_DRIFT")
        if not 0.995 <= geometry["rest_volume_ratio"] <= 1.005:
            rejected.append("REST_VOLUME_DRIFT")
        if geometry["symmetric_region_error_p95_stud"] > 0.002:
            rejected.append("SYMMETRY_DRIFT")

    rig = document["rigging"]
    if rig["max_influences_observed"] > 4:
        rejected.append("TOO_MANY_BONE_INFLUENCES")
    if rig["root_influenced_vertex_count"] > 0:
        rejected.append("ROOT_HAS_INFLUENCES")
    if rig["unweighted_deform_vertex_count"] > 0:
        rejected.append("UNWEIGHTED_DEFORM_VERTICES")
    if rig["normalized_weight_sum_error_max"] > 0.0001:
        rejected.append("WEIGHTS_NOT_NORMALIZED")
    if rig["weight_transfer_method"] == "automatic_weights" and "automatic_weights" not in auth["authorized_modifier_ops"]:
        rejected.append("UNVALIDATED_AUTOMATIC_WEIGHTS")

    operations = set(document.get("modifier_operations", []))
    unauthorized_forbidden = (operations & FORBIDDEN_DEFAULT) - set(auth["authorized_modifier_ops"])
    for op in sorted(unauthorized_forbidden):
        rejected.append(f"FORBIDDEN_OPERATION:{op}")

    if document["pipeline_id"] in {"r15_final_body", "dynamic_head"}:
        pose_by_id = {item["pose_id"]: item for item in document["pose_tests"]}
        missing_poses = REQUIRED_BODY_POSES - set(pose_by_id)
        for pose_id in sorted(missing_poses):
            blocked.append(f"POSE_MISSING:{pose_id}")
        for pose_id in sorted(REQUIRED_BODY_POSES & set(pose_by_id)):
            pose = pose_by_id[pose_id]
            if pose["status"] in {"BLOCKED", "NOT_RUN"}:
                blocked.append(f"POSE_NOT_AVAILABLE:{pose_id}")
                continue
            if pose["status"] == "FAIL":
                rejected.append(f"POSE_FAILED:{pose_id}")
            if not pose["evidence_ids"] or not set(pose["evidence_ids"]).issubset(evidence_ids):
                blocked.append(f"POSE_EVIDENCE_MISSING:{pose_id}")
            ratio = pose["joint_volume_retention_ratio"]
            intersections = pose["new_self_intersection_count"]
            if ratio is None or intersections is None:
                blocked.append(f"POSE_METRIC_MISSING:{pose_id}")
            else:
                if ratio < 0.90:
                    rejected.append(f"JOINT_VOLUME_COLLAPSE:{pose_id}")
                if intersections > 0:
                    rejected.append(f"POSE_SELF_INTERSECTION:{pose_id}")

    if rejected:
        status = "REJECTED"
        reasons = sorted(set(rejected + blocked))
    elif blocked:
        status = "BLOCKED"
        reasons = sorted(set(blocked))
    else:
        status = "APPROVED"
        reasons = []

    canonical = json.dumps(
        {
            "source_sha256": artifact["source_sha256"],
            "output_sha256": artifact["output_sha256"],
            "scope": scope,
            "status": status,
            "reason_codes": reasons,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "status": status,
        "reason_codes": reasons,
        "decision_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("contract_json", type=Path)
    args = parser.parse_args()
    document = json.loads(args.contract_json.read_text(encoding="utf-8"))
    result = evaluate(document, args.contract_json.parent)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "APPROVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
