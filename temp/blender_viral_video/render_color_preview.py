from pathlib import Path
source = Path('temp/blender_viral_video/render.py').read_text(encoding='utf-8')
source = source.replace(
    "m=bpy.data.materials.new(name); m.use_nodes=True",
    "m=bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True",
)
source = source.replace(
    "s.render.engine='BLENDER_EEVEE_NEXT';",
    "s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.studio_light='rim.sl';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='WORLD';s.display.shading.background_type='VIEWPORT';s.display.shading.background_color=(0.004,0.007,0.025);",
)
source = source.replace(
    "o.location=(0,-1.12,-4); o.scale=(.32,)*3",
    "o.location=(0,-0.78,-4); o.scale=(.14,)*3",
)
source = source.replace(
    "(1,16,br,btarget,(.2,-1.4,.55),(-.1,-.9,.5),82,'NÃO APERTE!'),",
    "(1,16,br,btarget,(-.6,-3.2,1.7),(-.2,-2.4,1.4),48,'NÃO APERTE!'),",
)
source = source.replace(
    "(17,31,avatar['root'],btarget,(1.1,1.8,2.1),(.55,1.15,1.8),48,'SÉRIO...'),",
    "(17,31,avatar['root'],btarget,(1.8,3.2,2.5),(1.1,2.3,2.1),42,'SÉRIO...'),",
)
source = source.replace(
    "(199,214,monster['root'],monster['target'],(.25,-1.55,2.1),(-.15,-1.05,1.95),78,'NÃO!'),",
    "(199,214,monster['root'],monster['target'],(.7,-3.2,2.7),(-.4,-2.2,2.35),55,'NÃO!'),",
)
exec(compile(source, 'render_color_preview_generated.py', 'exec'))
