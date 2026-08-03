from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

REQUIRED_EVIDENCE = {
    "renders/PROOF_EXPONENTIAL_DASHBOARD.png",
    "renders/PROOF_RESOLUTION_LADDER.png",
    "renders/PROOF_WORST_PYRAMID_CELLS.png",
    "renders/PROOF_SEMANTIC_VISIBILITY_MATRIX.png",
    "renders/PROOF_SEMANTIC_REGION_ZOOMS.png",
    "renders/PROOF_HEAD_INTERNALS_ISOLATED.png",
    "renders/PASS_BEAUTY_62.png",
    "renders/PASS_SILHOUETTE_62.png",
    "renders/PASS_NORMAL_62.png",
    "renders/PASS_SEMANTIC_62.png"
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def evaluate(document: dict[str, Any], root: Path) -> dict[str, Any]:
    rejected: list[str] = []
    blocked: list[str] = []
    warnings: list[str] = []
    artifact = root / document["artifact"]["path"]
    if not artifact.exists():
        blocked.append("ARTIFACT_MISSING")
    elif sha256_file(artifact) != document["artifact"]["sha256"]:
        rejected.append("ARTIFACT_HASH_MISMATCH")
    evidence_paths = {item["path"] for item in document["evidence"]}
    missing_required = sorted(REQUIRED_EVIDENCE - evidence_paths)
    if missing_required:
        blocked.append("REQUIRED_EVIDENCE_NOT_LISTED")
    for item in document["evidence"]:
        if item["artifact_sha256"] != document["artifact"]["sha256"]:
            rejected.append("EVIDENCE_ARTIFACT_MISMATCH")
            continue
        path = root / item["path"]
        if not path.exists():
            blocked.append("EVIDENCE_FILE_MISSING")
        elif sha256_file(path) != item["sha256"]:
            rejected.append("EVIDENCE_HASH_MISMATCH")
    c = document["coverage_model"]
    expected_total = (
        c["actual_rendered_view_passes"]
        + c["silhouette_multiscale_evaluations"]
        + c["appearance_multiscale_evaluations"]
        + c["silhouette_spatial_cells"]
        + c["appearance_spatial_cells"]
        + c["semantic_visibility_cells"]
    )
    if expected_total != c["total_quantitative_observations"]:
        rejected.append("COVERAGE_TOTAL_MISMATCH")
    if c["cells_per_image"] != sum(g * g for g in c["grid_levels"]):
        rejected.append("SPATIAL_PYRAMID_COUNT_MISMATCH")
    if document["structure"]["triangles"] + document["structure"]["triangle_margin"] != document["structure"]["triangle_limit"]:
        rejected.append("TRIANGLE_MARGIN_MISMATCH")
    if document["visual"]["ms_ssim_min"] < document["project_policy"]["thresholds"]["ms_ssim_min"]:
        warnings.append("MS_SSIM_BELOW_INTERNAL_POLICY")
    if document["visual"]["appearance_ssim_p05_all_cells"] < document["project_policy"]["thresholds"]["appearance_cell_p05_min"]:
        warnings.append("APPEARANCE_P05_BELOW_INTERNAL_POLICY")
    gates = document["external_gates"]
    all_external_pass = all(value == "PASS" for value in gates.values())
    if document["decision"]["release_eligible"] and not all_external_pass:
        rejected.append("FALSE_RELEASE_APPROVAL")
    if document["decision"]["status"] == "RELEASE_APPROVED" and not all_external_pass:
        rejected.append("RELEASE_STATUS_WITHOUT_EXTERNAL_GATES")
    if rejected:
        status = "REJECTED"
    elif blocked:
        status = "BLOCKED"
    elif all_external_pass:
        status = "RELEASE_APPROVED"
    elif warnings:
        status = "LOCAL_EXPONENTIAL_REVIEWED_WITH_WARNINGS"
    else:
        status = "LOCAL_EXPONENTIAL_REVIEWED"
    return {"status": status, "rejected": sorted(set(rejected)), "blocked": sorted(set(blocked)), "warnings": sorted(set(warnings)), "release_eligible": status == "RELEASE_APPROVED"}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--schema", type=Path, default=Path(__file__).parents[1] / "schemas" / "exponential_visual_contract.schema.json")
    args = parser.parse_args()
    document = json.loads(args.contract.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(document)
    root = args.root or args.contract.parents[1]
    result = evaluate(document, root)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"LOCAL_EXPONENTIAL_REVIEWED", "LOCAL_EXPONENTIAL_REVIEWED_WITH_WARNINGS", "RELEASE_APPROVED"} else 1
if __name__ == "__main__":
    raise SystemExit(main())
