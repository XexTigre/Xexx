from __future__ import annotations
import hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator
from src.exponential_visual_gate import evaluate

ROOT = Path(__file__).parents[1]
SCHEMA = json.loads((ROOT / "schemas/exponential_visual_contract.schema.json").read_text())

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture(tmp_path: Path):
    artifact = tmp_path / "artifact.glb"; artifact.write_bytes(b"glTF-test")
    ev=[]
    required=[
      "renders/PROOF_EXPONENTIAL_DASHBOARD.png","renders/PROOF_RESOLUTION_LADDER.png","renders/PROOF_WORST_PYRAMID_CELLS.png","renders/PROOF_SEMANTIC_VISIBILITY_MATRIX.png","renders/PROOF_SEMANTIC_REGION_ZOOMS.png","renders/PROOF_HEAD_INTERNALS_ISOLATED.png","renders/PASS_BEAUTY_62.png","renders/PASS_SILHOUETTE_62.png","renders/PASS_NORMAL_62.png","renders/PASS_SEMANTIC_62.png"]
    for rel in required:
        p=tmp_path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(rel.encode())
        ev.append({"path":rel,"sha256":sha(p),"size_bytes":p.stat().st_size,"artifact_sha256":sha(artifact)})
    d={
      "schema_version":"4.0.0","artifact":{"file":"artifact.glb","path":"artifact.glb","sha256":sha(artifact),"source_file":"source.glb","source_sha256":"0"*64,"pipeline":"avatar_setup_body_input_candidate"},
      "coverage_model":{"name":"power_of_two_spatial_visual_pyramid","canonical_views":62,"essential_passes_62":4,"extended_passes_12":8,"scale_factors":[1,2,4,8],"grid_levels":[1,2,4,8],"cells_per_image":85,"actual_rendered_view_passes":344,"silhouette_multiscale_evaluations":248,"appearance_multiscale_evaluations":48,"silhouette_spatial_cells":5270,"appearance_spatial_cells":1020,"semantic_visibility_cells":240,"total_quantitative_observations":7170},
      "structure":{"local_parser_errors":[],"geometry_nodes":20,"triangles":9864,"triangle_limit":10742,"triangle_margin":878,"dimensions_stud":[3.3,6.5,1.1],"node_transforms_identity":True},
      "geometry":{"physical_boundary_edges":0,"physical_nonmanifold_edges":0,"degenerate_triangles":0,"duplicate_face_groups":0,"render_boundary_edges":2610},
      "surface":{"normals_finite":True,"normal_length_min":0.999,"normal_length_max":1.0,"uv_outside_0_1_count":0,"uv_exact":{"nonzero_overlap_pairs":0,"status":"PASS"},"texture_byte_exact":True,"texture_sha256":"1"*64},
      "visual":{"appearance_ssim_p05_all_cells":0.98,"ms_ssim_min":0.99,"expected_semantic_contract_satisfied":True,"internal_components_present":{"MouthBag_Component":True,"UpperTeeth_Component":True,"LowerTeeth_Component":True,"Tongue_Component":True}},
      "project_policy":{"authority":"internal_project_policy_not_official_roblox","frozen":True,"thresholds":{"ms_ssim_min":0.95,"appearance_cell_p05_min":0.9}},
      "external_gates":{"khronos_gltf_validator":"NOT_RUN","blender_4_5_12_import_reopen_exact_artifact":"NOT_RUN","roblox_avatar_setup":"NOT_RUN","roblox_studio_playtest":"NOT_RUN","ugc_validation":"NOT_RUN"},
      "decision":{"status":"LOCAL_EXPONENTIAL_REVIEWED","release_eligible":False,"manual_override":False,"reason_codes":[]},"evidence":ev}
    Draft202012Validator(SCHEMA).validate(d)
    return d

def test_valid_local_review(tmp_path):
    d=fixture(tmp_path); assert evaluate(d,tmp_path)["status"]=="LOCAL_EXPONENTIAL_REVIEWED"
def test_tampered_evidence_rejected(tmp_path):
    d=fixture(tmp_path);(tmp_path/d["evidence"][0]["path"]).write_bytes(b"tamper");assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_missing_evidence_blocked(tmp_path):
    d=fixture(tmp_path);(tmp_path/d["evidence"][0]["path"]).unlink();assert evaluate(d,tmp_path)["status"]=="BLOCKED"
def test_false_release_rejected(tmp_path):
    d=fixture(tmp_path);d["decision"]["release_eligible"]=True;assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_coverage_mismatch_rejected(tmp_path):
    d=fixture(tmp_path);d["coverage_model"]["total_quantitative_observations"]-=1;assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_threshold_warning(tmp_path):
    d=fixture(tmp_path);d["visual"]["ms_ssim_min"]=0.90;assert evaluate(d,tmp_path)["status"]=="LOCAL_EXPONENTIAL_REVIEWED_WITH_WARNINGS"
def test_external_pass_release(tmp_path):
    d=fixture(tmp_path);d["external_gates"]={k:"PASS" for k in d["external_gates"]};assert evaluate(d,tmp_path)["status"]=="RELEASE_APPROVED"
def test_wrong_artifact_hash_rejected(tmp_path):
    d=fixture(tmp_path);d["artifact"]["sha256"]="f"*64;assert evaluate(d,tmp_path)["status"]=="REJECTED"
