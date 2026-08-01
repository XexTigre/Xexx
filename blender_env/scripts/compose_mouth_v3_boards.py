from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root)
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12);titlefont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24)
except:font=titlefont=ImageFont.load_default()
def board(folder,out,title,cols):
 files=sorted(Path(folder).glob('*.png'));ims=[Image.open(x).convert('RGB') for x in files];w,h=ims[0].size;rows=(len(ims)+cols-1)//cols;b=Image.new('RGB',(cols*w,rows*(h+24)+48),(8,8,10));d=ImageDraw.Draw(b);d.text((12,10),title,font=titlefont,fill='white')
 for i,(im,f) in enumerate(zip(ims,files)):x=(i%cols)*w;y=48+(i//cols)*(h+24);b.paste(im,(x,y));d.text((x+5,y+h+4),f.stem,font=font,fill='white')
 b.save(out)
board(root/'renders'/'neutral',root/'BLENDER_NEUTRAL_50_ANGLES.png','BLENDER 4.5.12 — BOCA NEUTRA 50 ÂNGULOS',10)
board(root/'renders'/'jawdrop',root/'BLENDER_JAWDROP_50_ANGLES.png','BLENDER 4.5.12 — JAWDROP 50 ÂNGULOS',10)
board(root/'renders'/'internal_jawdrop',root/'BLENDER_INTERNAL_JAWDROP_50_ANGLES.png','BLENDER 4.5.12 — INTERIOR JAWDROP 50 ÂNGULOS',10)
board(root/'renders'/'facs17',root/'BLENDER_FACS17_ALL_POSES.png','BLENDER 4.5.12 — NEUTRAL + 17 FACS',6)
files=[x for x in root.rglob('*') if x.is_file()];(root/'SHA256SUMS.txt').write_text('\n'.join(f"{hashlib.sha256(x.read_bytes()).hexdigest()}  {x.relative_to(root)}" for x in sorted(files) if x.name!='SHA256SUMS.txt')+'\n')
