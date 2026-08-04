from pathlib import Path

SRC = Path('temp/blender_viral_video/enhance_v2.py')
DST = Path('temp/blender_viral_video/enhance_v2_final.py')
s = SRC.read_text(encoding='utf-8')
s = s.replace('resolution_x=540', 'resolution_x=360')
s = s.replace('resolution_y=960', 'resolution_y=640')
s = s.replace("'resolution':[540,960]", "'resolution':[360,640]")
s = s.replace(
    "if hasattr(S.render,'use_motion_blur'):S.render.use_motion_blur=True",
    "if hasattr(S.render,'use_motion_blur'):S.render.use_motion_blur=False",
)
s = s.replace(
    "S.use_nodes=True;nt=S.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=.65;gl.size=6;comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],comp.inputs['Image'])",
    "S.use_nodes=False",
)
s = s.replace(
    "o.data.dof.use_dof=True;o.data.dof.aperture_fstop=3.0",
    "o.data.dof.use_dof=False",
)
anchor = "S['version']='2.0.0';"
fix_lines = [
    "S.view_settings.exposure=-.75",
    "camera_factors={1:3.2,2:2.2,3:1.35,4:1.25,5:1.25,6:2.5,7:2.5,8:2.25,9:1.6,10:1.3,11:2.2,12:1.15,13:2.7,14:1.8,15:3.2}",
    "for idx,factor in camera_factors.items():",
    " cam=bpy.data.objects.get(f'ShotCam{idx}')",
    " if not cam: continue",
    " cam.data.lens=min(cam.data.lens,44 if idx in {1,2,6,7,8,12,13,15} else 50)",
    " rig=cam.parent",
    " if not rig: continue",
    " rig.location*=factor",
    " if rig.animation_data and rig.animation_data.action:",
    "  for fc in rig.animation_data.action.fcurves:",
    "   if fc.data_path=='location':",
    "    for kp in fc.keyframe_points:",
    "     kp.co[1]*=factor;kp.handle_left[1]*=factor;kp.handle_right[1]*=factor",
    "for obj in bpy.data.objects:",
    " if obj.name.startswith(('Tower','V2Tower','V2Win')) and abs(obj.location.y)<8:",
    "  sign=1 if obj.location.y>=0 else -1",
    "  obj.location.y=sign*(8.5+abs(obj.location.y)*.25)",
    "for ld in bpy.data.lights: ld.energy*=.58",
    "for mat in bpy.data.materials:",
    " if mat.use_nodes:",
    "  pbs=mat.node_tree.nodes.get('Principled BSDF')",
    "  if pbs and 'Emission Strength' in pbs.inputs: pbs.inputs['Emission Strength'].default_value*=.62",
]
if anchor not in s:
    raise RuntimeError('Enhancer anchor not found')
s = s.replace(anchor, '\n'.join(fix_lines) + '\n' + anchor)
s = s.replace("S['version']='2.0.0'", "S['version']='2.0.2'")
s = s.replace("'version':'2.0.0'", "'version':'2.0.2'")
s = s.replace(
    "'classification']='native_eevee_3d_low_poly'",
    "'classification']='native_eevee_3d_low_poly_optimized_corrected'",
)
s = s.replace(
    "'native Eevee render','AgX','motion blur','DOF','glow compositor'",
    "'native Eevee render','AgX','corrected cameras','cleared camera corridor','post glow'",
)
DST.write_text(s, encoding='utf-8')
compile(s, str(DST), 'exec')
print(DST)
