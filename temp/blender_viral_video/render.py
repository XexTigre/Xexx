import bpy, math, json, os, random
from mathutils import Vector
from pathlib import Path

OUT = Path(os.environ.get('VIRAL_OUT', 'viral_output')).resolve()
FRAMES = OUT / 'frames'; FRAMES.mkdir(parents=True, exist_ok=True)
FPS=24; END=240


def mat(name, color, emit=0.0, metallic=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=color; p.inputs['Roughness'].default_value=.32; p.inputs['Metallic'].default_value=metallic
    if 'Emission Color' in p.inputs:
        p.inputs['Emission Color'].default_value=color; p.inputs['Emission Strength'].default_value=emit
    return m

def col(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c

def move(obj,c):
    for x in list(obj.users_collection): x.objects.unlink(obj)
    c.objects.link(obj)

def cube(name,loc,scale,m,c,parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m); o.parent=parent; move(o,c)
    b=o.modifiers.new('Bevel','BEVEL'); b.width=.04; b.segments=2
    return o

def cyl(name,loc,r,d,m,c,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=d,location=loc); o=bpy.context.object; o.name=name; o.data.materials.append(m); o.parent=parent; move(o,c); return o

def emp(name,c,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None); c.objects.link(o); o.parent=parent; o.location=loc; o.empty_display_type='SPHERE'; o.empty_display_size=.14; return o

def linear(o):
    if not o.animation_data or not o.animation_data.action:return
    for f in o.animation_data.action.fcurves:
        for k in f.keyframe_points:k.interpolation='LINEAR'

def visible(o,v,f):
    o.hide_render=not v; o.hide_viewport=not v; o.keyframe_insert(data_path='hide_render',frame=f); o.keyframe_insert(data_path='hide_viewport',frame=f)
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path in {'hide_render','hide_viewport'}:
                for k in fc.keyframe_points:k.interpolation='CONSTANT'

def track(o,t):
    q=o.constraints.new(type='TRACK_TO'); q.target=t; q.track_axis='TRACK_NEGATIVE_Z'; q.up_axis='UP_Y'

def build_char(name,primary,skin,accent,scale=1.0):
    c=col(name); root=emp(name+'Root',c); root.scale=(scale,)*3
    parts={
      'torso':cube(name+'Torso',(0,0,1.55),(.56,.34,.68),primary,c,root),
      'head':cube(name+'Head',(0,0,2.58),(.46,.45,.46),skin,c,root),
      'al':cube(name+'ArmL',(-.78,0,1.58),(.19,.22,.62),accent,c,root),
      'ar':cube(name+'ArmR',(.78,0,1.58),(.19,.22,.62),accent,c,root),
      'll':cube(name+'LegL',(-.29,0,.52),(.23,.28,.57),primary,c,root),
      'lr':cube(name+'LegR',(.29,0,.52),(.23,.28,.57),primary,c,root)}
    parts['root']=root; parts['target']=emp(name+'Target',c,root,(0,0,1.75)); return parts

def animate_char(p,path,cycles):
    r=p['root']
    for f,loc in path:r.location=loc;r.keyframe_insert(data_path='location',frame=f)
    linear(r)
    for i in range(int(cycles*4)+1):
        f=path[0][0]+round((path[-1][0]-path[0][0])*i/(cycles*4)); s=math.sin(2*math.pi*i/4)*.95
        for n,v in [('al',s),('ar',-s),('ll',-.78*s),('lr',.78*s)]:p[n].rotation_euler.x=v;p[n].keyframe_insert(data_path='rotation_euler',frame=f)
    for n in ('al','ar','ll','lr'):linear(p[n])

def caption(cam,text,start,end,index):
    c=col('Captions'); curve=bpy.data.curves.new('CaptionCurve'+str(index),'FONT'); curve.body=text; curve.align_x='CENTER'; curve.align_y='CENTER'; curve.size=1; curve.extrude=.025; curve.bevel_depth=.01
    o=bpy.data.objects.new('Caption'+str(index),curve); c.objects.link(o); o.parent=cam; o.location=(0,-1.12,-4); o.scale=(.32,)*3
    colors=[(1,.75,.02,1),(1,.03,.22,1),(.02,.55,1,1),(1,1,1,1)]; curve.materials.append(mat('CaptionMat'+str(index),colors[index%4],3.5))
    visible(o,False,max(1,start-1)); visible(o,True,start); visible(o,True,end); visible(o,False,min(END,end+1))

def camera(name,parent,target,offset1,offset2,lens,start,end,index):
    c=col('ShotCameras'); rig=emp(name+'Rig',c,parent,offset1); rig.keyframe_insert(data_path='location',frame=start); rig.location=offset2; rig.keyframe_insert(data_path='location',frame=end); linear(rig); track(rig,target)
    d=bpy.data.cameras.new(name); cam=bpy.data.objects.new(name,d); c.objects.link(cam); cam.parent=rig; d.lens=lens; d.dof.use_dof=True; d.dof.focus_object=target; d.dof.aperture_fstop=3.5
    mark=bpy.context.scene.timeline_markers.new(name,frame=start); mark.camera=cam
    if bpy.context.scene.camera is None:bpy.context.scene.camera=cam
    return cam

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene; s.render.engine='BLENDER_EEVEE_NEXT'; s.render.resolution_x=360; s.render.resolution_y=640; s.render.resolution_percentage=100; s.render.fps=FPS; s.frame_start=1; s.frame_end=END; s.render.image_settings.file_format='PNG'; s.render.filepath=str(FRAMES/'frame_'); s.world.color=(.002,.004,.015); s.render.film_transparent=False
try:s.view_settings.look='AgX - Medium High Contrast'
except:pass

dark=mat('Dark',(.01,.015,.045,1),0,.4); blue=mat('Blue',(.02,.35,1,1),4); pink=mat('Pink',(1,.01,.2,1),5); lava=mat('Lava',(1,.025,.002,1),5); skin=mat('Skin',(.94,.68,.42,1)); white=mat('White',(.8,.95,1,1),4)
e=col('Environment'); cube('Lava',(3,0,-1.2),(16,7,.3),lava,e); cube('Start',(-4.5,-1,-.25),(3.5,3,.25),dark,e); cube('Runway',(4,.2,.1),(7,1.15,.18),dark,e); cube('Exit',(10.7,0,.15),(1.7,2.6,.22),dark,e)
for side in (-1,1):cube('Rail'+str(side),(4,side*1.45,.18),(7,.045,.045),blue,e)
for i,x in enumerate((0,2.2,4.3,6.2,8.0)):
    cube('Step'+str(i),(x,.2,.25+(.32 if i%2 else 0)),(.65,1,.14),dark,e); pole=cyl('Pole'+str(i),(x,(-1 if i%2 else 1),1.35),.08,2.4,blue,e); pole.keyframe_insert(data_path='rotation_euler',frame=1); pole.rotation_euler.y=math.pi*(3+i*.4); pole.keyframe_insert(data_path='rotation_euler',frame=END); linear(pole)
for i in range(10):
    x=-1+i*1.25;y=(-1 if i%2 else 1)*(2.5+(i%3));o=cube('Tower'+str(i),(x,y,1.2+(i%4)*.3),(.35,.35,1.5+(i%4)*.3),pink if i%3==0 else dark,e);o.keyframe_insert(data_path='rotation_euler',frame=1);o.rotation_euler.z=math.pi*(1+(i%3));o.keyframe_insert(data_path='rotation_euler',frame=END);linear(o)

p=col('Props'); br=emp('ButtonRoot',p,None,(-3.25,-1,0)); cube('ButtonBase',(0,0,.25),(.7,.7,.25),dark,p,br); bt=cyl('ButtonTop',(0,0,.62),.48,.25,pink,p,br); btarget=emp('ButtonTarget',p,br,(0,0,.62)); bt.keyframe_insert(data_path='location',frame=1);bt.keyframe_insert(data_path='location',frame=29);bt.location.z=-.16;bt.keyframe_insert(data_path='location',frame=34);bt.keyframe_insert(data_path='location',frame=228);bt.location.z=0;bt.keyframe_insert(data_path='location',frame=236);linear(bt)
pr=emp('PortalRoot',p,None,(10.55,0,1.9)); ptarget=emp('PortalTarget',p,pr)
for i,r in enumerate((1.45,1.15,.82)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.11,major_segments=40,minor_segments=10,location=(0,0,0),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='PortalRing'+str(i);o.data.materials.append(blue if i%2==0 else white);o.parent=pr;move(o,p);o.scale=(.001,)*3;o.keyframe_insert(data_path='scale',frame=141);o.scale=(1,1,1);o.keyframe_insert(data_path='scale',frame=166+i*2);o.keyframe_insert(data_path='rotation_euler',frame=141);o.rotation_euler.z=math.pi*(3+i);o.keyframe_insert(data_path='rotation_euler',frame=END);linear(o)

avatar=build_char('Avatar',blue,skin,pink,1.0); ap=[(1,(-5.15,-1,0)),(16,(-4.75,-1,0)),(31,(-3.8,-1,0)),(43,(-3.35,-1,0)),(56,(-2.55,-.45,0)),(72,(-1.45,0,0)),(91,(.15,.3,0)),(108,(2,.25,0)),(124,(3.5,.3,0)),(132,(4.3,.3,1.15)),(141,(5.15,.3,0)),(158,(6.45,.25,0)),(177,(7.45,.15,0)),(198,(8.75,.05,0)),(214,(9.6,0,0)),(228,(10.65,0,0)),(240,(11,0,0))];animate_char(avatar,ap,10.5)
monster=build_char('Monster',mat('M1',(.08,.002,.12,1)),mat('M2',(.12,0,.18,1)),pink,1.75); mp=[(57,(-4.8,.7,-.1)),(72,(-3.2,.5,-.1)),(91,(-1,.45,-.1)),(108,(.9,.35,-.1)),(124,(2.6,.3,-.1)),(141,(4,.35,-.1)),(158,(5.55,.25,-.1)),(177,(6.9,.15,-.1)),(198,(8.25,.1,-.1)),(214,(9.15,0,-.1)),(228,(9.85,0,-.1)),(240,(10.1,0,-.1))];animate_char(monster,mp,8)
for o in monster.values():
    if isinstance(o,bpy.types.Object):visible(o,False,1);visible(o,False,55);visible(o,True,57)

lib=col('CameraLibrary'); lib['available']=30
for i in range(30):
    a=2*math.pi*i/30; rad=3.0+(i%5)*.65; rig=emp(f'PresetRig_{i+1:02d}',lib,avatar['root'],(math.cos(a)*rad,math.sin(a)*rad,1.0+(i%6)*.45));track(rig,avatar['target']);d=bpy.data.cameras.new(f'PresetCam_{i+1:02d}');cam=bpy.data.objects.new(d.name,d);lib.objects.link(cam);cam.parent=rig;d.lens=20+(i%10)*8;cam['preset_number']=i+1

shots=[
(1,16,br,btarget,(.2,-1.4,.55),(-.1,-.9,.5),82,'NÃO APERTE!'),
(17,31,avatar['root'],btarget,(1.1,1.8,2.1),(.55,1.15,1.8),48,'SÉRIO...'),
(32,43,br,btarget,(-2.5,-3.5,1.6),(-1.1,-1.8,1.2),28,'ELE APERTOU'),
(44,56,avatar['root'],avatar['target'],(-2.8,-3.5,2),(-1.3,-2.1,1.65),32,'CORRE!'),
(57,72,monster['root'],monster['target'],(-1,-2.2,.15),(.7,-1.4,.3),20,'O QUE É ISSO?!'),
(73,91,avatar['root'],avatar['target'],(.3,3.8,.45),(-.7,2.4,.7),22,'NÃO OLHA PRA TRÁS'),
(92,108,avatar['root'],avatar['target'],(-4.6,-.8,2),(-3,1.2,1.45),34,'MAIS RÁPIDO!'),
(109,124,avatar['root'],avatar['target'],(-1,-2.1,2.05),(.65,-1.55,1.75),45,'QUASE PEGOU'),
(125,141,avatar['root'],avatar['target'],(0,-.4,7.5),(1.4,.8,5.2),30,'PULA!'),
(142,158,pr,ptarget,(-4.5,-2.5,1.8),(4.2,-1.7,1.9),25,'UMA SAÍDA'),
(159,177,pr,ptarget,(4,-3,2.2),(-3,2.7,1.7),30,'A PORTA ABRIU!'),
(178,198,avatar['root'],avatar['target'],(-.4,-4.5,1.9),(.2,-2.3,1.5),36,'VAI!'),
(199,214,monster['root'],monster['target'],(.25,-1.55,2.1),(-.15,-1.05,1.95),78,'NÃO!'),
(215,228,pr,ptarget,(-2.5,-1.5,10),(2.5,1.5,8),42,'ESCAPOU?'),
(229,240,br,btarget,(.2,-1.4,.55),(-.1,-.9,.5),82,'VOCÊ APERTARIA?')]
for i,(st,en,par,tgt,o1,o2,lens,text) in enumerate(shots):
    cam=camera('ShotCam'+str(i+1),par,tgt,o1,o2,lens,st,en,i);caption(cam,text,st,en,i)
s['camera_library_count']=30;s['shot_count']=15;s['story']='button,monster,chase,portal,loop'

lc=col('Lights')
for name,loc,energy,color,target in [('BlueKey',(-2,-4,6),1500,(.05,.3,1),avatar['target']),('PinkRim',(5,4,5),1300,(1,.02,.2),avatar['target']),('ButtonLight',(-3,-2,2),900,(1,.01,.05),btarget),('PortalLight',(10,-1,3),1200,(.02,.5,1),ptarget)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.shape='DISK';d.size=3;o=bpy.data.objects.new(name,d);lc.objects.link(o);o.location=loc;track(o,target)
d=bpy.data.lights.new('Sun','SUN');d.energy=1.2;d.color=(.25,.35,1);o=bpy.data.objects.new('Sun',d);lc.objects.link(o);o.rotation_euler=(.5,-.3,-.5)

s.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'viral_button_chase.blend')); bpy.ops.render.render(animation=True)
print(json.dumps({'status':'OK','frames':END,'camera_library':30,'shot_cameras':15,'output':str(OUT)}))
