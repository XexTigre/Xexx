from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CANONICAL_VIEWS = {(yaw, pitch) for pitch in (-60, -30, 0, 30, 60) for yaw in range(0, 360, 30)} | {(0, 90), (0, -90)}
EXTERNAL_REQUIRED_FOR_RELEASE = (
    "khronos_gltf_validator",
    "blender_import_reopen",
    "roblox_avatar_setup",
    "roblox_studio_playtest",
    "ugc_validation",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate(document: dict[str, Any], root: Path) -> dict[str, Any]:
    blocked: list[str] = []
    rejected: list[str] = []

    artifact = document["artifact"]
    artifact_path = root / artifact["path"]
    if not artifact_path.is_file():
        blocked.append("ARTIFACT_MISSING")
    elif sha256_file(artifact_path) != artifact["sha256"]:
        rejected.append("ARTIFACT_HASH_MISMATCH")

    evidence_ids: set[str] = set()
    for item in document["evidence"]:
        if item["evidence_id"] in evidence_ids:
            rejected.append(f"DUPLICATE_EVIDENCE_ID:{item['evidence_id']}")
        evidence_ids.add(item["evidence_id"])
        path = root / item["path"]
        if not path.is_file():
            blocked.append(f"EVIDENCE_MISSING:{item['evidence_id']}")
            continue
        if sha256_file(path) != item["sha256"]:
            rejected.append(f"EVIDENCE_HASH_MISMATCH:{item['evidence_id']}")
        if item["artifact_sha256"] != artifact["sha256"]:
            rejected.append(f"EVIDENCE_WRONG_ARTIFACT:{item['evidence_id']}")

    review = document["review"]
    if len({review["generator_id"], review["validator_id"], review["reviewer_id"]}) != 3:
        rejected.append("SELF_CERTIFICATION")

    topology = document["topology"]
    if topology["physical_boundary_edges"] != 0:
        rejected.append("PHYSICAL_BOUNDARY_EDGES_PRESENT")
    if topology["physical_nonmanifold_edges"] != 0:
        rejected.append("PHYSICAL_NONMANIFOLD_EDGES_PRESENT")
    if topology["degenerate_triangles"] != 0:
        rejected.append("DEGENERATE_TRIANGLES_PRESENT")
    if topology["duplicate_face_groups"] != 0:
        rejected.append("DUPLICATE_FACES_PRESENT")

    texture = document["texture"]
    if not texture["embedded_image_byte_exact"]:
        rejected.append("TEXTURE_NOT_BYTE_EXACT")

    uv = document["uv"]
    if uv["uv_outside_0_1_count"] != 0:
        rejected.append("UV_OUTSIDE_0_1")
    if uv["exact_nonzero_overlap_pairs"] != 0 or uv["exact_overlap_area"] > uv["exact_overlap_tolerance_area"]:
        rejected.append("EXACT_UV_OVERLAP_PRESENT")
    # Raster multi-coverage is deliberately not an overlap gate because shared borders are counted.

    views = document["multiview"]["views"]
    view_keys = {(item["yaw"], item["pitch"]) for item in views}
    if len(views) != 62 or view_keys != CANONICAL_VIEWS:
        blocked.append("CANONICAL_62_VIEW_SET_INCOMPLETE")
    for item in views:
        if not item["evidence_ids"] or not set(item["evidence_ids"]).issubset(evidence_ids):
            blocked.append(f"VIEW_EVIDENCE_MISSING:{item['yaw']}:{item['pitch']}")
        if item["silhouette_iou"] < 0 or item["silhouette_iou"] > 1:
            rejected.append(f"VIEW_IOU_INVALID:{item['yaw']}:{item['pitch']}")

    metrics = document["multiview"]["summary"]
    if metrics["silhouette_iou_min"] < document["internal_policy"]["silhouette_iou_min"]:
        rejected.append("SILHOUETTE_POLICY_FAILED")
    if metrics["ssim_min"] < document["internal_policy"]["ssim_min"]:
        rejected.append("SSIM_POLICY_FAILED")

    external = document["external_gates"]
    release_requested = document["decision"]["release_eligible"]
    if release_requested:
        missing = [name for name in EXTERNAL_REQUIRED_FOR_RELEASE if external[name] != "PASS"]
        if missing:
            rejected.append("FALSE_RELEASE_APPROVAL:" + ",".join(missing))
    if document["decision"]["manual_override"]:
        rejected.append("MANUAL_OVERRIDE_FORBIDDEN")

    if rejected:
        status = "REJECTED"
        reasons = sorted(set(rejected + blocked))
    elif blocked:
        status = "BLOCKED"
        reasons = sorted(set(blocked))
    else:
        all_external = all(external[name] == "PASS" for name in EXTERNAL_REQUIRED_FOR_RELEASE)
        status = "RELEASE_APPROVED" if all_external and release_requested else "CANDIDATE_LOCAL_REVIEWED"
        reasons = []

    canonical = json.dumps(
        {"artifact_sha256": artifact["sha256"], "status": status, "reason_codes": reasons},
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
    return 0 if result["status"] in {"CANDIDATE_LOCAL_REVIEWED", "RELEASE_APPROVED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
