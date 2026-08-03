from __future__ import annotations
import bpy, json, math, hashlib, argparse, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def parse_args():
    argv=sys.argv
    argv=argv[argv.index('--')+1:] if '--' in argv else []
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);return p.parse_args(argv)

def world_vertices(obj):
    deps=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
    try:return [obj.matrix_world @ v.co for v in mesh.vertices]
    finally:ev.to_mesh_clear()

def center_of(obj):
    vs=world_vertices(obj);return sum(vs,Vector())/max(len(vs),1)

def bounds_of(objs):
    vs=[]
    for o in objs:vs.extend(world_vertices(o))
    mn=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)))
    mx=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)))
    return mn,mx

def proj_extreme(obj,axis):
    vals=[v.dot(axis) for v in world_vertices(obj)];return min(vals),max(vals)

def setup_render(outdir,head_objs):
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='WORLD';scene.display.shading.background_type='WORLD';scene.display.shading.single_color=(0.18,0.18,0.18)
    world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.color=(0.015,0.015,0.018)
    cam_data=bpy.data.cameras.new('MouthAuditCamera');cam=bpy.data.objects.new('MouthAuditCamera',cam_data);bpy.context.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO'
    mn,mx=bounds_of(head_objs);center=(mn+mx)*0.5;span=max((mx-mn).x,(mx-mn).y,(mx-mn).z);cam.data.ortho_scale=span*1.30
    return scene,cam,center,span

def set_camera(cam,center,front,up,yaw_deg,pitch_deg,dist):
    qy=Quaternion(up,math.radians(yaw_deg));d=qy@front;right=d.cross(up).normalized();qp=Quaternion(right,math.radians(pitch_deg));d=(qp@d).normalized();cam.location=center+d*dist;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()

def render_one(scene,path):
    path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def capture_pose_basis(arm, frame):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {pb.name: pb.matrix_basis.copy().decompose() for pb in arm.pose.bones}

def render_interpolated_motion(scene, arm, cam, cam_center, front, up, dist, outdir, target_frame, steps=31):
    """Render a neutral->target->neutral motion from actual imported pose-bone transforms."""
    action = arm.animation_data.action if arm.animation_data else None
    neutral = capture_pose_basis(arm, 0)
    target = capture_pose_basis(arm, target_frame)
    if arm.animation_data:
        arm.animation_data.action = None
    outdir.mkdir(parents=True, exist_ok=True)
    ts = [i / (steps - 1) for i in range(steps)] + [i / (steps - 1) for i in range(steps - 2, -1, -1)]
    for index, t in enumerate(ts):
        for pb in arm.pose.bones:
            l0, r0, s0 = neutral[pb.name]
            l1, r1, s1 = target[pb.name]
            loc = l0.lerp(l1, t)
            rot = r0.slerp(r1, t)
            scl = s0.lerp(s1, t)
            pb.matrix_basis = Matrix.LocRotScale(loc, rot, scl)
        bpy.context.view_layer.update()
        set_camera(cam, cam_center, front, up, 0, 0, dist)
        render_one(scene, outdir / f"{index:03d}.png")
    if arm.animation_data:
        arm.animation_data.action = action
    scene.frame_set(0)
    bpy.context.view_layer.update()

def main():
    a=parse_args();inp=Path(a.input).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);(out/'renders').mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(inp))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    by={o.name:o for o in meshes};required=['Head_Geo_Input','UpperLip_Component','LowerLip_Component','MouthBag_Component','UpperTeeth_Component','LowerTeeth_Component','Tongue_Component','LeftEye_Component','RightEye_Component']
    missing=[n for n in required if n not in by]
    if missing:raise RuntimeError('Missing mouth objects: '+','.join(missing))
    if len(arms)!=1:raise RuntimeError(f'Expected one armature, got {len(arms)}')
    arm=arms[0];bones=arm.data.bones
    head=by['Head_Geo_Input'];frame_map={f'Frame{i}':head.get(f'Frame{i}') for i in range(18)}
    required_poses=['Neutral','LeftEyeClosed','RightEyeClosed','EyesLookDown','JawDrop','Pucker','LeftLipCornerPuller','RightLipCornerPuller','ChinRaiser','ChinRaiserUpperLip','LeftCheekRaiser','RightCheekRaiser','LeftInnerBrowRaiser','RightInnerBrowRaiser','LeftLipCornerDown','RightLipCornerDown','LeftLowerLipDepressor','RightLowerLipDepressor']
    mapped=[frame_map[f'Frame{i}'] for i in range(18)]
    root_face=head.get('RootFaceJoint')
    max_inf=0;max_sum_err=0.0;root_weighted=0;unweighted=0
    for o in meshes:
        root_idx=o.vertex_groups.get('Root').index if o.vertex_groups.get('Root') else None
        for v in o.data.vertices:
            weights=[g.weight for g in v.groups if g.weight>1e-8];max_inf=max(max_inf,len(weights));s=sum(weights);max_sum_err=max(max_sum_err,abs(s-1.0));unweighted+=int(s<1e-8)
            if root_idx is not None:root_weighted+=sum(1 for g in v.groups if g.group==root_idx and g.weight>1e-8)
    tri=sum(sum(max(len(p.vertices)-2,0) for p in o.data.polygons) for o in meshes)
    head_center=center_of(head);lip_center=(center_of(by['UpperLip_Component'])+center_of(by['LowerLip_Component']))*0.5;front=(lip_center-head_center).normalized();up=Vector((0,0,1))
    if abs(front.dot(up))>0.9:up=Vector((0,1,0))
    head_objs=[by[n] for n in required];scene,cam,cam_center,span=setup_render(out,head_objs);dist=span*3.0
    scene.frame_set(0);bpy.context.view_layer.update();lip_front=max(proj_extreme(by['UpperLip_Component'],front)[1],proj_extreme(by['LowerLip_Component'],front)[1]);internal_front={n:proj_extreme(by[n],front)[1] for n in ['MouthBag_Component','UpperTeeth_Component','LowerTeeth_Component','Tongue_Component']};neutral_occluded=all(v<lip_front-0.01 for v in internal_front.values())
    scene.frame_set(0);bpy.context.view_layer.update();neutral_centers={n:center_of(by[n]) for n in ['UpperLip_Component','LowerLip_Component','UpperTeeth_Component','LowerTeeth_Component','Tongue_Component']}
    scene.frame_set(4);bpy.context.view_layer.update();jaw_centers={n:center_of(by[n]) for n in neutral_centers};movement={n:float((jaw_centers[n]-neutral_centers[n]).length) for n in neutral_centers}
    jaw_motion_ok=movement['LowerLip_Component']>0.02 and movement['LowerTeeth_Component']>0.02 and movement['Tongue_Component']>0.02 and movement['UpperLip_Component']<0.01 and movement['UpperTeeth_Component']<0.01
    angles=[(yaw,pitch) for pitch in [-40,-20,0,20,40] for yaw in range(0,360,36)]
    for frame,label in [(0,'neutral'),(4,'jawdrop')]:
        scene.frame_set(frame);bpy.context.view_layer.update();folder=out/'renders'/label
        for i,(yaw,pitch) in enumerate(angles):set_camera(cam,cam_center,front,up,yaw,pitch,dist);render_one(scene,folder/f'{i:02d}_yaw{yaw:03d}_pitch{pitch:+03d}.png')
    facs=out/'renders'/'facs17'
    for frame,name in enumerate(required_poses):scene.frame_set(frame);bpy.context.view_layer.update();set_camera(cam,cam_center,front,up,0,0,dist);render_one(scene,facs/f'{frame:02d}_{name}.png')
    scene.frame_set(4);bpy.context.view_layer.update();external_hide=[o for o in meshes if o.name not in ['MouthBag_Component','UpperTeeth_Component','LowerTeeth_Component','Tongue_Component']]
    for o in external_hide:o.hide_render=True
    old_color=scene.display.shading.color_type;scene.display.shading.color_type='OBJECT';colors={'MouthBag_Component':(0.35,0.02,0.04,1),'UpperTeeth_Component':(0.95,0.92,0.80,1),'LowerTeeth_Component':(0.86,0.84,0.72,1),'Tongue_Component':(0.65,0.06,0.12,1)}
    for n,c in colors.items():by[n].color=c
    folder=out/'renders'/'internal_jawdrop'
    for i,(yaw,pitch) in enumerate(angles):set_camera(cam,cam_center,front,up,yaw,pitch,dist);render_one(scene,folder/f'{i:02d}_yaw{yaw:03d}_pitch{pitch:+03d}.png')
    for o in external_hide:o.hide_render=False
    scene.display.shading.color_type=old_color
    render_interpolated_motion(scene, arm, cam, cam_center, front, up, dist, out/'renders'/'motion_jawdrop', 4, 31)
    render_interpolated_motion(scene, arm, cam, cam_center, front, up, dist, out/'renders'/'motion_pucker', 5, 31)
    blend=out/'RBX_ANIME_DOLL_3D_MOUTH_V3_IMPORTED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    roundtrip=out/'RBX_ANIME_DOLL_3D_MOUTH_V3_BLENDER_ROUNDTRIP.glb';bpy.ops.export_scene.gltf(filepath=str(roundtrip),export_format='GLB',export_animations=True,export_extras=True,export_yup=True)
    checks={
      'required_objects_present':not missing,'root_face_joint_mapped':root_face=='DynamicHead','facs_mapping_exact':mapped==required_poses,'armature_count_one':len(arms)==1,
      'joint_count':len(bones),'joint_count_under_roblox_recommendation':len(bones)<67,'max_influences_le_4':max_inf<=4,'weight_sums_normalized':max_sum_err<=1e-4,'root_weights_zero':root_weighted==0,'unweighted_vertices_zero':unweighted==0,
      'triangle_budget':tri<=10742,'neutral_internals_occluded':neutral_occluded,'jaw_motion_expected':jaw_motion_ok,'no_decal_named_objects':not any('decal' in o.name.lower() for o in meshes),'no_preexisting_cage_objects':not any('cage' in o.name.lower() for o in meshes),
      'neutral_render_count':len(list((out/'renders'/'neutral').glob('*.png')))==50,'jawdrop_render_count':len(list((out/'renders'/'jawdrop').glob('*.png')))==50,'internal_render_count':len(list((out/'renders'/'internal_jawdrop').glob('*.png')))==50,'facs_render_count':len(list((out/'renders'/'facs17').glob('*.png')))==18,'jawdrop_motion_frame_count':len(list((out/'renders'/'motion_jawdrop').glob('*.png')))==61,'pucker_motion_frame_count':len(list((out/'renders'/'motion_pucker').glob('*.png')))==61,
    }
    critical=[k for k,v in checks.items() if isinstance(v,bool) and not v]
    report={'schema_version':'1.0.0','artifact':{'path':str(inp),'sha256':sha(inp)},'blender':{'version':bpy.app.version_string,'build_hash':bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash,bytes) else str(bpy.app.build_hash)},'inventory':{'mesh_objects':len(meshes),'armatures':len(arms),'joints':len(bones),'triangles':tri,'actions':len(bpy.data.actions)},'mapping':{'RootFaceJoint':root_face,'frames':mapped},'weights':{'max_influences':max_inf,'max_sum_error':max_sum_err,'root_weighted_assignments':root_weighted,'unweighted_vertices':unweighted},'mouth':{'front_axis_blender':list(front),'neutral_lip_front_projection':lip_front,'neutral_internal_front_projection':internal_front,'jawdrop_movement_stud':movement},'checks':checks,'critical_failures':critical,'status':'PASS' if not critical else 'FAIL','outputs':{'blend':str(blend),'roundtrip_glb':str(roundtrip)}}
    (out/'BLENDER_MOUTH_V3_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if critical:raise RuntimeError('Blender mouth validation failures: '+','.join(critical))

if __name__=='__main__':main()
