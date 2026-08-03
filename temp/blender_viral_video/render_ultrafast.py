from pathlib import Path
source = Path('temp/blender_viral_video/render.py').read_text(encoding='utf-8')
source = source.replace("s.render.engine='BLENDER_EEVEE_NEXT';", "s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='FLAT';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;s.display.shading.show_cavity=False;")
source = source.replace("s.render.resolution_x=360; s.render.resolution_y=640;", "s.render.resolution_x=180; s.render.resolution_y=320;")
exec(compile(source, 'render_ultrafast_generated.py', 'exec'))
