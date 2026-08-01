from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROFILE_BOUNDS = {
    "Normal": {"x": (1.35, 8.6), "y": (3.6, 9.5), "z": (0.7, 2.25)},
    "Slender": {"x": (1.35, 6.0), "y": (3.6, 9.5), "z": (0.7, 2.0)},
    "Classic": {"x": (1.35, 8.0), "y": (3.6, 9.1), "z": (0.7, 2.0)},
}

REQUIRED_PASSES = {
    "beauty", "flat_albedo", "silhouette", "wireframe",
    "normal", "uv_checker", "seam_heatmap",
}

METRIC_RULES = {
    "silhouette_iou": (">=", 0.97),
    "contour_chamfer_px": ("<=", 1.5),
    "ssim": (">=", 0.95),
    "lpips": ("<=", 0.08),
    "delta_e_2000_p95": ("<=", 5.0),
    "seam_band_delta_e_2000_p95": ("<=", 3.0),
    "mirror_delta_e_2000_p95": ("<=", 4.0),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compare(value: float, op: str, threshold: float) -> bool:
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    return value == threshold


def evaluate(document: dict[str, Any], root: Path) -> dict[str, Any]:
    blocked: list[str] = []
    rejected: list[str] = []

    asset = document["asset"]
    artifact_path = root / asset["artifact_path"]
    if not artifact_path.is_file():
        blocked.append("ARTIFACT_MISSING")
    elif sha256_file(artifact_path) != asset["sha256"]:
        rejected.append("ARTIFACT_HASH_MISMATCH")

    evidence_by_id = {item["evidence_id"]: item for item in document["evidence"]}
    for item in document["evidence"]:
        path = root / item["path"]
        if not path.is_file():
            blocked.append(f"EVIDENCE_MISSING:{item['evidence_id']}")
            continue
        if sha256_file(path) != item["sha256"]:
            rejected.append(f"EVIDENCE_HASH_MISMATCH:{item['evidence_id']}")
        if item["artifact_sha256"] != asset["sha256"]:
            rejected.append(f"EVIDENCE_WRONG_ARTIFACT:{item['evidence_id']}")

    coord = document["coordinate_contract"]
    expected = "-Z" if asset["pipeline"] == "avatar_setup_input" else "+Z"
    if coord["required_front_axis"] != expected:
        rejected.append("CONTRACT_FRONT_AXIS_INCORRECT")
    if coord["asset_front_axis"] != coord["required_front_axis"]:
        rejected.append("ASSET_FRONT_AXIS_MISMATCH")
    if not coord["centered_on_y_axis"]:
        rejected.append("ASSET_NOT_CENTERED")

    scale = document["scale_contract"]
    bounds = PROFILE_BOUNDS[scale["profile"]]
    for axis in ("x", "y", "z"):
        value = scale["bounds"][axis]
        lo, hi = bounds[axis]
        if not lo <= value <= hi:
            rejected.append(f"SCALE_{axis.upper()}_OUT_OF_PROFILE")
    if not scale["node_transform_baked"]:
        rejected.append("TRANSFORM_NOT_BAKED")

    if asset["triangles"] > 10742:
        rejected.append("TRIANGLE_BUDGET_EXCEEDED")
    geometry = document["geometry"]
    if not geometry["watertight"] or geometry["boundary_edge_count"] > 0:
        rejected.append("GEOMETRY_NOT_WATERTIGHT")
    if geometry["non_manifold_edge_count"] > 0:
        rejected.append("NON_MANIFOLD_EDGES")
    if geometry["pose"] not in {"A", "T"}:
        rejected.append("POSE_NOT_A_OR_T")

    render = document["render_protocol"]
    required_view_count = 62 if render["mode"] == "intensive_62" else 12
    if len(render["views"]) < required_view_count:
        blocked.append("RENDER_VIEW_SET_INCOMPLETE")
    if not REQUIRED_PASSES.issubset(set(render["passes"])):
        blocked.append("RENDER_PASSES_INCOMPLETE")
    if render["clipped_pixels"] != 0:
        rejected.append("RENDER_CLIPPING")
    if not 0.025 <= render["crop_margin_ratio"] <= 0.035:
        rejected.append("NON_DETERMINISTIC_CROP_MARGIN")

    uv = document["uv_contract"]
    if uv["overlap_area_ratio"] > 0.0:
        rejected.append("UV_OVERLAP")
    if uv["island_min_gutter_px"] < 16.0:
        rejected.append("UV_GUTTER_TOO_SMALL")
    if uv["texture_border_clearance_px"] < 16.0:
        rejected.append("UV_BORDER_CLEARANCE_TOO_SMALL")
    if uv["bleed_px"] < 8.0:
        rejected.append("UV_BLEED_TOO_SMALL")
    if asset["pipeline"] in {"avatar_setup_input", "r15_final", "dynamic_head_final"}:
        if uv["texture_width_px"] > 2048 or uv["texture_height_px"] > 2048:
            rejected.append("AVATAR_TEXTURE_TOO_LARGE")

    for name, (expected_op, expected_threshold) in METRIC_RULES.items():
        metric = document["pixel_metrics"][name]
        if metric["status"] in {"BLOCKED", "NOT_RUN"} or metric["value"] is None:
            blocked.append(f"METRIC_UNAVAILABLE:{name}")
            continue
        missing = [eid for eid in metric["evidence_ids"] if eid not in evidence_by_id]
        if missing:
            blocked.append(f"METRIC_EVIDENCE_MISSING:{name}")
            continue
        if metric["comparison"] != expected_op or metric["threshold"] != expected_threshold:
            rejected.append(f"METRIC_POLICY_CHANGED:{name}")
        elif not compare(float(metric["value"]), expected_op, expected_threshold):
            rejected.append(f"METRIC_FAILED:{name}")

    review = document["review"]
    identities = {review["generator_id"], review["validator_id"], review["reviewer_id"]}
    if len(identities) != 3:
        rejected.append("SELF_CERTIFICATION")

    if document["decision"]["manual_override"]:
        rejected.append("MANUAL_OVERRIDE_FORBIDDEN")

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
        {"asset_sha256": asset["sha256"], "status": status, "reason_codes": reasons},
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
    parser.add_argument("audit_json", type=Path)
    args = parser.parse_args()
    document = json.loads(args.audit_json.read_text(encoding="utf-8"))
    result = evaluate(document, args.audit_json.parent)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "APPROVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
