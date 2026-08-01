from pathlib import Path
import json,sys
R=Path(__file__).parents[1];sys.path.insert(0,str(R));from src.orientation_50view_gate import evaluate
def f():return json.load(open(R/"contracts/RBX_ANIME_DOLL_V15_orientation_50view_contract.json"))
def test_real():assert evaluate(f(),R)["status"]=="LOCAL_BLENDER_50VIEW_REVIEWED"
def test_back():d=f();d["orientation"]["yaw0_semantic"]="BACK";assert evaluate(d,R)["status"]=="REJECTED"
def test_49():d=f();d["blender_proof"]["regions"][0]["raw_views"].pop();assert evaluate(d,R)["status"]=="REJECTED"
def test_eye():d=f();d["blender_proof"]["regions"]=[x for x in d["blender_proof"]["regions"] if x["region_id"]!="left_eye"];assert evaluate(d,R)["status"]=="REJECTED"
def test_sym():d=f();d["symmetry"]["measurements"]["arms"]["p95"]=1;assert evaluate(d,R)["status"]=="REJECTED"
def test_release():d=f();d["decision"]["release_eligible"]=True;assert evaluate(d,R)["status"]=="REJECTED"
def test_missing():d=f();d["blender_proof"]["regions"][0]["raw_views"][0]["path"]="missing";assert evaluate(d,R)["status"]=="BLOCKED"
def test_hash():d=f();d["artifact"]["sha256"]="f"*64;assert evaluate(d,R)["status"]=="REJECTED"
