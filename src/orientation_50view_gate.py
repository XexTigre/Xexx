from pathlib import Path
import hashlib,json,sys
REGIONS=["full_body","head","left_eye","right_eye","mouth_external","mouth_internal","neck","upper_torso","lower_torso","left_arm","right_arm","left_hand","right_hand","left_upper_leg","right_upper_leg","left_lower_leg","right_lower_leg","left_foot","right_foot"]
Y=[0,36,72,108,144,180,216,252,288,324];P=[-40,-20,0,20,40]
def sha(p):
 h=hashlib.sha256();f=open(p,"rb")
 for b in iter(lambda:f.read(1048576),b""):h.update(b)
 f.close();return h.hexdigest()
def evaluate(d,root):
 root=Path(root);rej=[];blk=[]
 def ev(x,label):
  p=root/x["path"]
  if not p.is_file():blk.append(label+"_MISSING:"+x["path"]);return
  if sha(p)!=x["sha256"]:rej.append(label+"_HASH")
 ev(d["artifact"],"ARTIFACT");ev(d["orientation"]["source_failure_screenshot"],"SCREENSHOT")
 if d["orientation"]["yaw0_semantic"]!="FRONT" or d["orientation"]["yaw180_semantic"]!="BACK":rej.append("ORIENTATION")
 g=d["geometry"]
 if g["degenerate_triangles"] or g["physical_nonmanifold_edges_total"] or g["unexpected_boundary_edges"]:rej.append("GEOMETRY")
 if not d["symmetry"]["all_pass"] or any(float(v["p95"])>d["symmetry"]["policy_p95_stud_max"] for v in d["symmetry"]["measurements"].values()):rej.append("SYMMETRY")
 bp=d["blender_proof"];ids=[r["region_id"] for r in bp["regions"]]
 if sorted(ids)!=sorted(REGIONS) or bp["raw_render_count"]!=950:rej.append("REGIONS")
 want={(y,p) for p in P for y in Y}
 for r in bp["regions"]:
  ev({"path":r["board_path"],"sha256":r["board_sha256"]},"BOARD_"+r["region_id"]);pairs={(v["yaw"],v["pitch"]) for v in r["raw_views"]}
  if len(r["raw_views"])!=50 or pairs!=want:rej.append("VIEW_MATRIX_"+r["region_id"])
  for v in r["raw_views"]:ev(v,"VIEW_"+r["region_id"])
 for x in bp["proof_boards"]:ev(x,"PROOF")
 ev(bp["blend"],"BLEND");ev(bp["roundtrip"],"ROUNDTRIP")
 allplat=all(v=="PASS" for v in d["platform_gates"].values())
 if d["decision"]["release_eligible"] and not allplat:rej.append("FALSE_RELEASE")
 s="REJECTED" if rej else ("BLOCKED" if blk else ("RELEASE_APPROVED" if allplat else "LOCAL_BLENDER_50VIEW_REVIEWED"))
 return {"status":s,"rejected":sorted(set(rej)),"blocked":sorted(set(blk)),"release_eligible":s=="RELEASE_APPROVED"}
if __name__=="__main__":
 p=Path(sys.argv[1]);r=Path(sys.argv[2]) if len(sys.argv)>2 else p.parents[1];x=evaluate(json.load(open(p)),r);print(json.dumps(x,indent=2));raise SystemExit(0 if x["status"] in ["LOCAL_BLENDER_50VIEW_REVIEWED","RELEASE_APPROVED"] else 1)
