import bpy, math, json, os, random
from pathlib import Path
from mathutils import Vector

OUT=Path(os.environ.get('V2_OUT','viral_v2_output')).resolve(); (OUT/'frames').mkdir(parents=True,exist_ok=True)
S=bpy.context.scene; END=240

def C(name):
 c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
 if c.name not in S.collection.children: S.collection.children.link(c)
 return c

def M(name,color,metal=.0,rough=.35,emit=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=color; p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 if 'Emission Color' in p.inputs: p.inputs['Emission Color'].default_value=color; p.inputs['Emission Strength'].default_value=emit
 return m

def move(o,c):
 for x in list(o.users_collection): x.objects.unlink(o)
 c.objects.link(o)

def cube(name,loc,scale,mat,c,parent=None,bev=.06):
 bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(mat); o.parent=parent; move(o,c)
 if bev: b=o.modifiers.new('Bevel','BEVEL'); b.width=bev; b.segments=3
 return o

def sphere(name,loc,r,mat,c,parent=None,scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=r,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(mat); o.parent=parent; move(o,c)
 for p in o.data.polygons:p.use_smooth=True
 return o

def cyl(name,loc,r,d,mat,c,parent=None,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=d,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(mat); o.parent=parent; move(o,c)
 for p in o.data.polygons:p.use_smooth=True
 return o

def vis(o,v,f):
 o.hide_render=not v;o.hide_viewport=not v;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   if fc.data_path in {'hide_render','hide_viewport'}:
    for k in fc.keyframe_points:k.interpolation='CONSTANT'

def track(o,t):
 q=o.constraints.new('TRACK_TO');q.target=t;q.track_axis='TRACK_NEGATIVE_Z';q.up_axis='UP_Y'

S.render.engine='BLENDER_EEVEE_NEXT';S.render.resolution_x=540;S.render.resolution_y=960;S.render.resolution_percentage=100;S.render.fps=24;S.frame_start=1;S.frame_end=END;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.filepath=str(OUT/'frames'/'frame_');S.render.film_transparent=False
if hasattr(S.render,'use_motion_blur'):S.render.use_motion_blur=True
try:S.view_settings.look='AgX - Medium High Contrast'
except:pass
S.world.use_nodes=True; bg=S.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.001,.003,.012,1);bg.inputs['Strength'].default_value=.22
S.use_nodes=True;nt=S.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=.65;gl.size=6;comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],comp.inputs['Image'])

blue=M('V2_Blue',(.01,.22,1,1),.3,.22,2.2);pink=M('V2_Pink',(1,.005,.16,1),.2,.2,3.4);cyan=M('V2_Cyan',(.01,.65,1,1),.15,.18,4);orange=M('V2_Orange',(1,.08,.002,1),.1,.22,4);dark=M('V2_Dark',(.006,.01,.025,1),.75,.2);skin=M('V2_Skin',(.92,.5,.25,1),0,.48);white=M('V2_White',(.9,.98,1,1),0,.16,3)
for o in bpy.data.objects:
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
  if not any(m.type=='BEVEL' for m in o.modifiers):
   b=o.modifiers.new('V2Bevel','BEVEL');b.width=.025;b.segments=2
 if o.type=='CAMERA':
  o.data.dof.use_dof=True;o.data.dof.aperture_fstop=3.0

for n,m in [('Blue',blue),('Pink',pink),('Lava',orange),('Dark',dark),('Skin',skin),('White',white),('M1',dark),('M2',pink)]:
 old=bpy.data.materials.get(n)
 if old:
  for o in bpy.data.objects:
   if o.type=='MESH':
    for i,x in enumerate(o.data.materials):
     if x==old:o.data.materials[i]=m

fx=C('V2_FX');env=C('V2_Environment');detail=C('V2_CharacterDetail');rng=random.Random(240804)
cube('V2_BackFloor',(3,0,-1.45),(17,8,.12),dark,env,bev=.08)
for x in range(-7,16):cube('GridX'+str(x),(x,0,-1.3),(.015,7,.015),cyan,env,bev=.005)
for y in range(-7,8):cube('GridY'+str(y),(4,y,-1.3),(11,.015,.015),pink if y%3==0 else cyan,env,bev=.005)
for i in range(48):
 x=rng.uniform(-9,17);y=rng.choice((-1,1))*rng.uniform(4,11);h=rng.uniform(2,9);w=rng.uniform(.35,1.3);cube('V2Tower%02d'%i,(x,y,h/2-1),(w,w*.7,h/2),dark,env,bev=.05)
 for z in range(1,int(h),2):cube('V2Win%02d_%02d'%(i,z),(x,y-rng.choice((-.72,.72))*w,z-.6),(w*.5,.02,.12),cyan if i%2 else pink,env,bev=.01)

ar=bpy.data.objects.get('AvatarRoot');mr=bpy.data.objects.get('MonsterRoot')
if ar:
 sphere('AvatarHair',(0,.04,2.92),.52,dark,detail,ar,scale=(1.05,.92,.58));sphere('AvatarEyeL',(-.17,-.47,2.65),.065,cyan,detail,ar,scale=(.8,.35,1.2));sphere('AvatarEyeR',(.17,-.47,2.65),.065,cyan,detail,ar,scale=(.8,.35,1.2));cube('AvatarMouth',(0,-.49,2.43),(.13,.025,.025),pink,detail,ar,bev=.015)
 for s in (-1,1):sphere('AvatarHand'+str(s),(s*.79,-.02,.93),.22,skin,detail,ar);cube('AvatarShoe'+str(s),(s*.29,-.15,-.12),(.28,.42,.16),dark,detail,ar,bev=.1)
 cube('AvatarBackpack',(0,.43,1.58),(.42,.18,.52),pink,detail,ar,bev=.14)
if mr:
 for s in (-1,1):
  sphere('MonsterEye'+str(s),(s*.28,-.82,4.48),.11,pink,detail,mr,scale=(.75,.3,1.25));cyl('MonsterHorn'+str(s),(s*.52,0,4.95),.12,.9,dark,detail,mr,rot=(0,s*.65,0))
 for i in range(6):cyl('Claw'+str(i),(((i%3)-1)*.16,-.5,1.1+(i//3)*.08),.035,.52,white,detail,mr,rot=(math.pi/2,0,0))

for i,(x,y,f) in enumerate(((1.5,.7,91),(5.2,-.6,141),(8.3,.4,190))):
 s=sphere('Shard'+str(i+1),(x,y,1.55),.42,(cyan,pink,orange)[i],fx,scale=(.55,.25,1.25));s.keyframe_insert('rotation_euler',frame=1);s.rotation_euler=(math.tau*2,math.tau*3,math.tau*4);s.keyframe_insert('rotation_euler',frame=END);s.keyframe_insert('scale',frame=f-2);s.scale=(2,2,2);s.keyframe_insert('scale',frame=f);vis(s,True,1);vis(s,True,f);vis(s,False,f+1)
for i in range(36):
 line=cyl('Streak%02d'%i,(rng.uniform(-2,11),rng.uniform(-1.3,1.3),rng.uniform(.2,3.5)),.018,rng.uniform(.5,1.6),cyan if i%3 else pink,fx,rot=(0,math.pi/2,0));vis(line,False,1);vis(line,True,56);vis(line,True,220);vis(line,False,221)

pr=bpy.data.objects.get('PortalRoot')
if pr:
 for i,r in enumerate((1.7,1.36,1.02,.7)):
  bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.055,major_segments=48,minor_segments=10,location=(0,0,0),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='V2Portal'+str(i);o.data.materials.append((cyan,white,pink,orange)[i]);o.parent=pr;move(o,fx);o.scale=(.001,)*3;o.keyframe_insert('scale',frame=140);o.scale=(1,1,1);o.keyframe_insert('scale',frame=165+i*2);o.keyframe_insert('rotation_euler',frame=140);o.rotation_euler.z=math.tau*(2+i);o.keyframe_insert('rotation_euler',frame=END)
lr=bpy.data.objects.new('LaserRig',None);fx.objects.link(lr);lr.location=(4.7,.2,1.35)
for i in (-1,0,1):cyl('Laser'+str(i),(0,0,i*.65),.055,3.3,pink,fx,lr,rot=(math.pi/2,0,0))
lr.keyframe_insert('rotation_euler',frame=1);lr.rotation_euler.y=math.tau*5;lr.keyframe_insert('rotation_euler',frame=END)

lc=C('V2_Lights')
def light(name,typ,loc,energy,color,size=3,target=None):
 d=bpy.data.lights.new(name,typ);d.energy=energy;d.color=color
 if typ=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);lc.objects.link(o);o.location=loc
 if target:track(o,target)
 return o
at=bpy.data.objects.get('AvatarTarget');mt=bpy.data.objects.get('MonsterTarget');pt=bpy.data.objects.get('PortalTarget')
light('V2Key','AREA',(-2,-4,7),1250,(.03,.28,1),4,at);light('V2Rim','AREA',(5,4,6),1150,(1,.01,.16),3,at);light('V2Monster','AREA',(3,-3,4),950,(.5,.01,1),3,mt);light('V2PortalLight','AREA',(10,-2,4),1300,(.02,.6,1),3,pt);sun=light('V2Sun','SUN',(0,0,0),1.4,(.18,.26,.55));sun.rotation_euler=(.55,-.3,-.7)

for o in bpy.data.objects:
 if o.type=='CAMERA':o.data.clip_start=.03;o.data.clip_end=250
 if o.name.startswith('ShotCam') and o.parent and o.parent.animation_data and o.parent.animation_data.action:
  for fc in o.parent.animation_data.action.fcurves:
   if fc.data_path=='location':md=fc.modifiers.new('NOISE');md.strength=.018;md.scale=7
 if o.name.startswith('Caption'):o.scale*=1.18

S['version']='2.0.0';S['camera_library_count']=30;S['active_shot_count']=15;S['classification']='native_eevee_3d_low_poly';S.frame_set(1)
manifest={'version':'2.0.0','frames':240,'fps':24,'resolution':[540,960],'camera_library':30,'active_shots':15,'objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'improvements':['native Eevee render','AgX','motion blur','DOF','glow compositor','character detail','48-building skyline','3 collectible shards','laser obstacle','enhanced portal','per-camera review'], 'limits':['low-poly rigid-part character','virality not guaranteed']}
(OUT/'scene_manifest.v2.0.0.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'viral_button_chase_v2.blend'));bpy.ops.render.render(animation=True)
print(json.dumps(manifest))
