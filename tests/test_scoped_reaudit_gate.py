from __future__ import annotations
import hashlib
from pathlib import Path
from src.scoped_reaudit_gate import evaluate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base(tmp_path: Path, scope: str="avatar_setup_input_readiness") -> dict:
    asset=tmp_path/"asset.glb"; asset.write_bytes(b"glb")
    evidence=tmp_path/"audit.json"; evidence.write_text("{}")
    ah=digest(asset)
    return {
      "contract_version":"1.3.0","artifact":{"path":asset.name,"sha256":ah},"pipeline_id":"avatar_setup_body_input","requested_scope":scope,"enforce_project_quality":False,
      "measurements":{"container_parse_ok":True,"khronos_validator_status":"PASS","mesh_object_count":1,"connected_component_count":6,"classified_component_count":6,"unknown_component_count":0,"triangle_count":9000,"boundary_edge_count":100,"unexpected_boundary_edge_count":0,"non_manifold_edge_count":0,"transform_identity":True,"front_axis":"-Z","up_axis":"+Y","pose":"A","centered_on_y_axis":True,"distinct_neck_status":"PASS","accessory_geometry_absent_status":"PASS","head_components_status":"PASS","texture_present":True,"body_part_mesh_count":0,"rig_present":False,"outer_cage_count":0,"attachment_count":0,"studio_import_status":"NOT_RUN","studio_playtest_status":"NOT_RUN","ugc_validation_status":"NOT_RUN","material_double_sided":False,"uv_gutter_px_2048":1.0,"uv_border_clearance_px_2048":1.0},
      "component_manifest":[
        {"component_id":"body","classification":"body_shell","face_count":8000,"boundary_edge_count":0,"allowed_open_boundary":False},
        {"component_id":"eye_l","classification":"left_eye","face_count":200,"boundary_edge_count":20,"allowed_open_boundary":True},
        {"component_id":"eye_r","classification":"right_eye","face_count":200,"boundary_edge_count":20,"allowed_open_boundary":True},
        {"component_id":"teeth_u","classification":"upper_teeth","face_count":200,"boundary_edge_count":20,"allowed_open_boundary":True},
        {"component_id":"teeth_l","classification":"lower_teeth","face_count":200,"boundary_edge_count":20,"allowed_open_boundary":True},
        {"component_id":"tongue","classification":"tongue","face_count":200,"boundary_edge_count":20,"allowed_open_boundary":True}
      ],
      "baseline_defects":[],
      "evidence":[{"evidence_id":"audit","path":evidence.name,"sha256":digest(evidence),"artifact_sha256":ah,"evidence_type":"mesh_audit_report","subject_ids":["container_parse","avatar_setup_input_readiness","component_manifest","pose","distinct_neck","accessory_geometry_absent","head_components"],"tool":"test","tool_version":"1"}],
      "review":{"generator_id":"g","validator_id":"v","reviewer_id":"r"},"decision":{"manual_override":False}
    }


def test_avatar_setup_input_can_have_no_rig(tmp_path: Path):
    result=evaluate(base(tmp_path),tmp_path)
    assert result["status"]=="SATISFIED"
    assert result["release_eligible"] is False


def test_current_style_fragmentation_fails(tmp_path: Path):
    d=base(tmp_path); m=d["measurements"]
    m.update({"connected_component_count":139,"classified_component_count":0,"unknown_component_count":139,"boundary_edge_count":2684,"unexpected_boundary_edge_count":2684,"front_axis":"+Z","pose":"UNKNOWN"})
    d["component_manifest"]=[{"component_id":f"c{i}","classification":"unknown","face_count":1,"boundary_edge_count":2684 if i==0 else 0,"allowed_open_boundary":False} for i in range(139)]
    result=evaluate(d,tmp_path)
    assert result["status"]=="FAILED"
    assert "UNCLASSIFIED_CONNECTED_COMPONENTS" in result["reason_codes"]
    assert "UNEXPECTED_OPEN_BOUNDARIES" in result["reason_codes"]


def test_low_uv_padding_is_project_warning_not_official_failure(tmp_path: Path):
    result=evaluate(base(tmp_path),tmp_path)
    assert result["status"]=="SATISFIED"
    assert "PROJECT_UV_GUTTER_BELOW_POLICY" in result["warnings"]


def test_enforced_project_uv_policy_fails(tmp_path: Path):
    d=base(tmp_path); d["enforce_project_quality"]=True
    assert evaluate(d,tmp_path)["status"]=="FAILED"


def test_khronos_scope_blocks_when_not_run(tmp_path: Path):
    d=base(tmp_path,"gltf_spec_validation"); d["measurements"]["khronos_validator_status"]="NOT_RUN"
    result=evaluate(d,tmp_path)
    assert result["status"]=="BLOCKED"
    assert "KHRONOS_VALIDATOR_NOT_RUN" in result["reason_codes"]


def test_preservation_does_not_imply_release(tmp_path: Path):
    d=base(tmp_path,"preservation"); d["baseline_defects"]=["OPEN_MESH"]
    d["evidence"][0]["evidence_type"]="preservation_report"; d["evidence"][0]["subject_ids"]=["preservation"]
    result=evaluate(d,tmp_path)
    assert result["status"]=="SATISFIED"
    assert result["release_eligible"] is False
    assert "PRESERVATION_DOES_NOT_CLEAR_BASELINE_DEFECTS" in result["warnings"]


def test_r15_requires_parts_rig_cages_and_attachments(tmp_path: Path):
    d=base(tmp_path,"r15_final_readiness"); d["pipeline_id"]="r15_final_body"; d["measurements"]["front_axis"]="+Z"
    result=evaluate(d,tmp_path)
    assert result["status"]=="FAILED"
    assert "R15_BODY_PART_COUNT_NOT_15" in result["reason_codes"]
    assert "R15_RIG_MISSING" in result["reason_codes"]


def test_studio_scope_requires_specific_evidence(tmp_path: Path):
    d=base(tmp_path,"studio_playtest")
    result=evaluate(d,tmp_path)
    assert result["status"]=="BLOCKED"
    assert "STUDIO_TEST_NOT_RUN" in result["reason_codes"]


def test_ugc_release_only_after_ugc_evidence(tmp_path: Path):
    d=base(tmp_path,"ugc_marketplace")
    result=evaluate(d,tmp_path)
    assert result["status"]=="BLOCKED" and result["release_eligible"] is False


def test_self_certification_fails(tmp_path: Path):
    d=base(tmp_path); d["review"]["reviewer_id"]="g"
    assert evaluate(d,tmp_path)["status"]=="FAILED"


def test_component_manifest_cannot_be_fabricated_by_summary(tmp_path: Path):
    d=base(tmp_path)
    d["measurements"]["connected_component_count"]=1
    result=evaluate(d,tmp_path)
    assert result["status"]=="FAILED"
    assert "COMPONENT_MANIFEST_COUNT_MISMATCH" in result["reason_codes"]
