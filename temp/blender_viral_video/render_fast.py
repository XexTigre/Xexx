from pathlib import Path
source = Path('temp/blender_viral_video/render.py').read_text(encoding='utf-8')
source = source.replace("s.render.engine='BLENDER_EEVEE_NEXT';", "s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='WORLD';")
exec(compile(source, 'render_fast_generated.py', 'exec'))
