from pathlib import Path
import hashlib,sys
R=Path(__file__).parents[1];sys.path.insert(0,str(R));from src.orientation_50view_gate import evaluate
REGIONS=["full_body","head","left_eye","right_eye","mouth_external","mouth_internal","neck","upper_torso","lower_torso","left_arm","right_arm","left_hand","right_hand","left_upper_leg","right_upper_leg","left_lower_leg","right_lower_leg","left_foot","right_foot"]
Y=[0,36,72,108,144,180,216,252,288,324];P=[-40,-20,0,20,40]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixture(tmp_path):
 artifact=tmp_path/"asset.glb";artifact.write_bytes(b"glTF-test")
 evidence=tmp_path/"evidence.bin";evidence.write_bytes(b"proof")
 ev={"path":evidence.name,"sha256":digest(evidence)}
 regions=[]
 for region in REGIONS:
  views=[{"path":evidence.name,"sha256":digest(evidence),"yaw":y,"pitch":p} for p in P for y in Y]
  regions.append({"region_id":region,"view_count":50,"board_path":evidence.name,"board_sha256":digest(evidence),"raw_views":views})
 return {"artifact":{"path":artifact.name,"sha256":digest(artifact),"triangles":9000,"triangle_limit":10742,"mesh_count":22},"orientation":{"yaw0_semantic":"FRONT","yaw180_semantic":"BACK","source_failure_screenshot":ev},"geometry":{"degenerate_triangles":0,"physical_nonmanifold_edges_total":0,"unexpected_boundary_edges":0},"symmetry":{"all_pass":True,"policy_p95_stud_max":0.001,"measurements":{"arms":{"p95":0.0}}},"blender_proof":{"raw_render_count":950,"regions":regions,"proof_boards":[ev,ev,ev],"blend":ev,"roundtrip":ev},"platform_gates":{"roblox_avatar_setup_exact_hash":"NOT_RUN","roblox_studio_playtest_exact_hash":"NOT_RUN","ugc_marketplace_validation":"NOT_RUN"},"decision":{"release_eligible":False}}
def test_valid(tmp_path):assert evaluate(fixture(tmp_path),tmp_path)["status"]=="LOCAL_BLENDER_50VIEW_REVIEWED"
def test_back(tmp_path):d=fixture(tmp_path);d["orientation"]["yaw0_semantic"]="BACK";assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_49(tmp_path):d=fixture(tmp_path);d["blender_proof"]["regions"][0]["raw_views"].pop();assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_eye(tmp_path):d=fixture(tmp_path);d["blender_proof"]["regions"]=[x for x in d["blender_proof"]["regions"] if x["region_id"]!="left_eye"];assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_sym(tmp_path):d=fixture(tmp_path);d["symmetry"]["measurements"]["arms"]["p95"]=1;assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_release(tmp_path):d=fixture(tmp_path);d["decision"]["release_eligible"]=True;assert evaluate(d,tmp_path)["status"]=="REJECTED"
def test_missing(tmp_path):d=fixture(tmp_path);d["blender_proof"]["regions"][0]["raw_views"][0]["path"]="missing";assert evaluate(d,tmp_path)["status"]=="BLOCKED"
def test_hash(tmp_path):d=fixture(tmp_path);d["artifact"]["sha256"]="f"*64;assert evaluate(d,tmp_path)["status"]=="REJECTED"
