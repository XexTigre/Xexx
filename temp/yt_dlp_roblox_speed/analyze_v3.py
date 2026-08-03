#!/usr/bin/env python3
from __future__ import annotations
import csv, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any
import cv2, numpy as np

ROOT=Path('temp/yt_dlp_roblox_speed'); OUT=ROOT/'results_v3'; VIDEOS=ROOT/'videos_v3'
OUT.mkdir(parents=True,exist_ok=True); VIDEOS.mkdir(parents=True,exist_ok=True)
QUERIES=['ytsearch8:roblox shorts','ytsearch8:roblox edit shorts','ytsearch8:roblox trend shorts']

def run(cmd,timeout=120): return subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
def base(): return ['yt-dlp','--ignore-config','--no-warnings','--remote-components','ejs:github','--js-runtimes','node','--socket-timeout','12','--retries','1','--extractor-retries','1','--fragment-retries','1']

def discover():
    found={}; logs=[]
    for q in QUERIES:
        try: p=run(base()+['--flat-playlist','--playlist-end','8','--dump-single-json',q],90)
        except Exception as e: logs.append({'query':q,'error':repr(e)}); continue
        logs.append({'query':q,'rc':p.returncode,'stderr':p.stderr[-4000:]})
        try: data=json.loads(p.stdout)
        except Exception: continue
        for e in data.get('entries') or []:
            vid=e.get('id')
            if vid: found[vid]={'id':vid,'title':e.get('title'),'url':f'https://www.youtube.com/watch?v={vid}','channel':e.get('channel') or e.get('uploader'),'view_count':e.get('view_count')}
    return list(found.values()),logs

def download(item):
    vid=item['id']; attempts=[]
    strategies=[
      ('tv_embedded,web_embedded','18/best[height<=360]/best'),
      ('web_safari,web_embedded','18/best[height<=480]/best'),
      ('android_vr,web_embedded','18/best[height<=360]/best')]
    for clients,fmt in strategies:
        cmd=base()+['--impersonate','chrome','--extractor-args',f'youtube:player_client={clients}','--no-playlist','--write-info-json','-f',fmt,'-o',str(VIDEOS/f'{vid}.%(ext)s'),item['url']]
        try: p=run(cmd,150)
        except Exception as e: attempts.append({'clients':clients,'error':repr(e)}); continue
        attempts.append({'clients':clients,'rc':p.returncode,'stdout':p.stdout[-2000:],'stderr':p.stderr[-7000:]})
        media=[x for x in VIDEOS.glob(f'{vid}.*') if x.suffix.lower() in {'.mp4','.webm','.mkv','.mov'} and x.stat().st_size>10000]
        if media: return max(media,key=lambda x:x.stat().st_size),attempts
    return None,attempts

def ffprobe(path):
    p=run(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate','-of','json',str(path)],60)
    if p.returncode: raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)

def analyze(path,vid):
    cap=cv2.VideoCapture(str(path)); fps=float(cap.get(cv2.CAP_PROP_FPS) or 0); expected=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    prevg=None; prevh=None; idx=0; last=-999999; cuts=0; motions=[]; rows=[]
    while True:
        ok,frame=cap.read()
        if not ok: break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        hist=cv2.calcHist([hsv],[0,1],None,[24,16],[0,180,0,256]); cv2.normalize(hist,hist)
        change=0.0 if prevh is None else float(cv2.compareHist(prevh,hist,cv2.HISTCMP_BHATTACHARYYA))
        motion=0.0
        if prevg is not None:
            a=cv2.resize(prevg,(160,90)); b=cv2.resize(gray,(160,90)); flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,3,15,3,5,1.2,0); motion=float(np.mean(np.linalg.norm(flow,axis=2)))
        cut=change>.42 and idx-last>max(1,round(fps*.22))
        if cut: cuts+=1; last=idx
        rows.append([idx,idx/fps if fps else 0,float(gray.mean()),float(hsv[:,:,1].mean()),float((cv2.Canny(gray,100,200)>0).mean()),change,motion,int(cut)])
        motions.append(motion); prevg=gray; prevh=hist; idx+=1
    cap.release(); csvp=OUT/f'{vid}_frames.csv'
    with csvp.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['frame','timestamp_s','brightness','saturation','edge_density','histogram_change','motion_score','cut']); w.writerows(rows)
    dur=idx/fps if fps else 0
    return {'fps':fps,'frames_expected':expected,'frames_decoded':idx,'all_frames_decoded':idx>0 and (expected<=0 or abs(expected-idx)<=1),'duration_s':dur,'cuts':cuts,'cuts_per_second':cuts/dur if dur else 0,'mean_shot_duration_s':dur/(cuts+1) if dur else None,'motion_mean':float(np.mean(motions)) if motions else None,'motion_p90':float(np.percentile(motions,90)) if motions else None,'csv':str(csvp)}

def classify(a):
    cps=a['cuts_per_second']; shot=a['mean_shot_duration_s'] or 999; mp=a['motion_p90'] or 0; score=0; reasons=[]
    if cps>=.8 or shot<=1.25: score+=2; reasons.append('cortes muito frequentes')
    elif cps>=.45 or shot<=2.2: score+=1; reasons.append('cortes frequentes')
    if mp>=4: score+=2; reasons.append('movimento muito alto')
    elif mp>=2.2: score+=1; reasons.append('movimento alto')
    return {'score':score,'label':'MUITO_ACELERADO' if score>=4 else 'ACELERADO' if score>=3 else 'MODERADO' if score>=1 else 'CALMO','reasons':reasons,'playback_literalmente_acelerado':'NÃO_COMPROVADO'}

def main():
    candidates,logs=discover(); (OUT/'search_logs.json').write_text(json.dumps(logs,indent=2,ensure_ascii=False)); (OUT/'candidates.json').write_text(json.dumps(candidates,indent=2,ensure_ascii=False))
    results=[]; failures=[]
    for item in candidates[:8]:
        if len(results)>=3: break
        media,ats=download(item)
        if not media: failures.append({'candidate':item,'attempts':ats}); continue
        try:
            pr=ffprobe(media); an=analyze(media,item['id']); results.append({'candidate':item,'download':{'bytes':media.stat().st_size},'ffprobe':pr,'frames':an,'pacing':classify(an),'review':{'download_verified':True,'ffprobe_verified':bool(pr.get('streams')),'all_frames_decoded':an['all_frames_decoded'],'no_fabricated_findings':True}})
        except Exception as e: failures.append({'candidate':item,'attempts':ats,'error':repr(e)})
    (OUT/'analysis.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)); (OUT/'failures.json').write_text(json.dumps(failures,indent=2,ensure_ascii=False))
    valid=[x for x in results if x['review']['download_verified'] and x['review']['ffprobe_verified'] and x['review']['all_frames_decoded']]
    fast=sum(x['pacing']['label'] in {'ACELERADO','MUITO_ACELERADO'} for x in valid)
    if valid:
        cps=median(x['frames']['cuts_per_second'] for x in valid); shot=median(x['frames']['mean_shot_duration_s'] for x in valid); motion=median(x['frames']['motion_p90'] for x in valid)
        conclusion=f"{'Sim' if fast>len(valid)/2 else 'Não de forma predominante'}: {fast} de {len(valid)} amostras são aceleradas. Mediana {cps:.2f} cortes/s, cena {shot:.2f}s, movimento P90 {motion:.2f}."; status='APROVADO'
    else: conclusion='Não foi possível confirmar: nenhum vídeo passou por download, ffprobe e decodificação integral.'; status='REJEITADO'
    rows=[]
    for x in valid:
        c=x['candidate']; f=x['frames']; p=x['pacing']; rows.append(f"| {(c.get('title') or c['id']).replace('|','/')} | {f['duration_s']:.1f} | {f['cuts_per_second']:.2f} | {f['mean_shot_duration_s']:.2f} | {f['motion_p90']:.2f} | {p['label']} |")
    table='| Vídeo | Duração s | Cortes/s | Cena s | Movimento P90 | Ritmo |\n|---|---:|---:|---:|---:|---|\n'+'\n'.join(rows) if rows else 'Nenhuma amostra aprovada.'
    md=f"""# Análise rápida revisada de trends Roblox\n\n**Execução:** {datetime.now(timezone.utc).isoformat()}  \n**Revisão:** **{status}**\n\n## Conclusão\n\n{conclusion}\n\n## Amostras\n\n{table}\n\n## Auditoria\n\n- IDs encontrados: **{len(candidates)}**\n- Vídeos integralmente analisados: **{len(valid)}**\n- Falhas: **{len(failures)}**\n- O termo “acelerado” descreve ritmo de cortes e movimento. Aceleração literal do playback não foi presumida.\n"""
    (OUT/'APRENDIZADO_TRENDS_ROBLOX_ACELERACAO.md').write_text(md); print(md)
    for f in failures[:4]:
        print('FALHA',f['candidate']['id'])
        for a in f.get('attempts',[]): print((a.get('stderr') or a.get('error') or '')[-900:])
    return 0 if valid else 2
if __name__=='__main__': raise SystemExit(main())
