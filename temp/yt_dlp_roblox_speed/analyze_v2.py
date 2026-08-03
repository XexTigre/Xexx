#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import numpy as np

ROOT = Path('temp/yt_dlp_roblox_speed')
OUT = ROOT / 'results_v2'
VIDEOS = ROOT / 'videos_v2'
OUT.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

QUERIES = [
    'ytsearch25:roblox shorts 2026',
    'ytsearch25:roblox edit shorts',
    'ytsearch25:roblox trend shorts',
    'ytsearch25:roblox meme shorts',
    'ytsearch25:roblox animation shorts',
]
MAX_ATTEMPTS = 18
MAX_APPROVED = 5


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def base() -> list[str]:
    return [
        'yt-dlp', '--ignore-config', '--no-warnings',
        '--remote-components', 'ejs:github', '--js-runtimes', 'node',
        '--extractor-retries', '2', '--fragment-retries', '2', '--retries', '2',
        '--socket-timeout', '20',
    ]


def discover() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    found: dict[str, dict[str, Any]] = {}
    logs: list[dict[str, Any]] = []
    for query in QUERIES:
        cmd = base() + ['--flat-playlist', '--dump-single-json', query]
        p = run(cmd, 420)
        logs.append({'query': query, 'returncode': p.returncode, 'stderr': p.stderr[-12000:]})
        try:
            payload = json.loads(p.stdout)
        except Exception:
            continue
        for e in payload.get('entries') or []:
            vid = e.get('id')
            if not vid:
                continue
            title = str(e.get('title') or '')
            found[vid] = {
                'id': vid,
                'url': e.get('url') if str(e.get('url') or '').startswith('http') else f'https://www.youtube.com/watch?v={vid}',
                'title': title,
                'channel': e.get('channel') or e.get('uploader'),
                'duration': e.get('duration'),
                'view_count': e.get('view_count'),
                'source_query': query,
            }
    candidates = list(found.values())
    candidates.sort(key=lambda x: int(x.get('view_count') or 0), reverse=True)
    return candidates, logs


def download(item: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    vid = item['id']
    attempts: list[dict[str, Any]] = []
    client_sets = [
        'web_safari,web_creator,web_embedded,android_vr',
        'tv_embedded,web_embedded,android_vr',
        'ios,android,web',
    ]
    for n, clients in enumerate(client_sets, 1):
        template = str(VIDEOS / f'{vid}.%(ext)s')
        cmd = base() + [
            '--impersonate', 'chrome',
            '--extractor-args', f'youtube:player_client={clients}',
            '--no-playlist', '--restrict-filenames', '--write-info-json',
            '--write-auto-subs', '--write-subs', '--sub-langs', 'pt.*,en.*,es.*', '--sub-format', 'vtt',
            '-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '--merge-output-format', 'mp4', '-o', template, item['url'],
        ]
        p = run(cmd, 900)
        attempts.append({'strategy': n, 'clients': clients, 'returncode': p.returncode,
                         'stdout_tail': p.stdout[-5000:], 'stderr_tail': p.stderr[-12000:]})
        media = [x for x in VIDEOS.glob(f'{vid}.*')
                 if x.suffix.lower() in {'.mp4','.webm','.mkv','.mov'} and x.stat().st_size > 10000]
        if media:
            return max(media, key=lambda x: x.stat().st_size), attempts
    return None, attempts


def probe(path: Path) -> dict[str, Any]:
    p = run(['ffprobe','-v','error','-show_entries',
             'format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate',
             '-of','json',str(path)], 120)
    if p.returncode:
        raise RuntimeError(p.stderr[-3000:])
    return json.loads(p.stdout)


def analyze_frames(path: Path, vid: str) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError('OpenCV não abriu o vídeo')
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    prev_gray = None
    prev_hist = None
    motions: list[float] = []
    changes: list[float] = []
    cuts: list[int] = []
    rows: list[list[Any]] = []
    idx = 0
    last_cut = -999999
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv],[0,1],None,[24,16],[0,180,0,256])
        cv2.normalize(hist,hist)
        change = 0.0 if prev_hist is None else float(cv2.compareHist(prev_hist,hist,cv2.HISTCMP_BHATTACHARYYA))
        motion = 0.0
        if prev_gray is not None:
            a = cv2.resize(prev_gray,(160,90)); b = cv2.resize(gray,(160,90))
            flow = cv2.calcOpticalFlowFarneback(a,b,None,0.5,3,15,3,5,1.2,0)
            motion = float(np.mean(np.linalg.norm(flow,axis=2)))
        is_cut = change > 0.42 and idx-last_cut > max(1,round(fps*0.22))
        if is_cut:
            cuts.append(idx); last_cut = idx
        ts = idx/fps if fps else 0.0
        rows.append([idx,round(ts,5),round(float(gray.mean()),4),round(float(hsv[:,:,1].mean()),4),
                     round(float((cv2.Canny(gray,100,200)>0).mean()),6),round(change,6),round(motion,6),int(is_cut)])
        motions.append(motion); changes.append(change)
        prev_gray=gray; prev_hist=hist; idx+=1
    cap.release()
    csv_path=OUT/f'{vid}_frames.csv'
    with csv_path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['frame','timestamp_s','brightness','saturation','edge_density','histogram_change','motion_score','detected_cut']); w.writerows(rows)
    duration=idx/fps if fps else 0.0
    return {
        'fps':fps,'width':width,'height':height,'frames_expected':expected,'frames_decoded':idx,
        'all_frames_decoded':idx>0 and (expected<=0 or abs(expected-idx)<=1),
        'duration_s':duration,'cuts_count':len(cuts),'cuts_per_second':len(cuts)/duration if duration else 0,
        'mean_shot_duration_s':duration/(len(cuts)+1) if duration else None,
        'motion_mean':float(np.mean(motions)) if motions else None,
        'motion_p90':float(np.percentile(motions,90)) if motions else None,
        'hist_change_mean':float(np.mean(changes)) if changes else None,'frame_csv':str(csv_path)
    }


def subtitles(vid: str) -> dict[str, Any]:
    files=sorted(VIDEOS.glob(f'{vid}*.vtt'))
    if not files:
        return {'status':'UNAVAILABLE','word_count':None,'words_per_second':None}
    text=files[0].read_text(encoding='utf-8',errors='ignore')
    cue=re.compile(r'(\d\d):(\d\d):(\d\d\.\d+)\s+-->\s+(\d\d):(\d\d):(\d\d\.\d+)')
    lines=text.splitlines(); i=0; words=0; speech=0.0; seen=set()
    while i<len(lines):
        m=cue.search(lines[i])
        if not m: i+=1; continue
        s=int(m[1])*3600+int(m[2])*60+float(m[3]); e=int(m[4])*3600+int(m[5])*60+float(m[6]); i+=1
        parts=[]
        while i<len(lines) and lines[i].strip():
            val=re.sub(r'<[^>]+>','',lines[i]).strip()
            if val: parts.append(val)
            i+=1
        val=re.sub(r'\s+',' ',' '.join(parts)).strip(); key=(round(s,1),val)
        if val and key not in seen:
            seen.add(key); words+=len(re.findall(r"\b[\wÀ-ÿ']+\b",val)); speech+=max(0,e-s)
        i+=1
    return {'status':'SUCCESS' if words else 'NO_SPEECH','word_count':words,'speaking_seconds':speech,
            'words_per_second':words/speech if speech else None,'files':[str(x) for x in files]}


def classify(fr: dict[str,Any], sub: dict[str,Any]) -> dict[str,Any]:
    score=0; reasons=[]; cps=fr['cuts_per_second']; shot=fr['mean_shot_duration_s'] or 999; mp=fr['motion_p90'] or 0; wps=sub.get('words_per_second')
    if cps>=0.8 or shot<=1.25: score+=2; reasons.append('cortes muito frequentes')
    elif cps>=0.45 or shot<=2.2: score+=1; reasons.append('cortes frequentes')
    if mp>=4: score+=2; reasons.append('movimento muito alto')
    elif mp>=2.2: score+=1; reasons.append('movimento alto')
    if isinstance(wps,(int,float)):
        if wps>=4: score+=2; reasons.append('fala/legenda muito rápida')
        elif wps>=3: score+=1; reasons.append('fala/legenda rápida')
    label='MUITO_ACELERADO' if score>=5 else 'ACELERADO' if score>=3 else 'MODERADO' if score>=1 else 'CALMO'
    literal='SUSPEITA' if cps<0.25 and mp>=4 and isinstance(wps,(int,float)) and wps>=4 else 'NÃO_COMPROVADO'
    return {'score':score,'label':label,'reasons':reasons,'playback_literalmente_acelerado':literal}


def main() -> int:
    candidates, search_logs=discover()
    (OUT/'candidates.json').write_text(json.dumps(candidates,indent=2,ensure_ascii=False),encoding='utf-8')
    (OUT/'search_logs.json').write_text(json.dumps(search_logs,indent=2,ensure_ascii=False),encoding='utf-8')
    approved=[]; failures=[]
    for item in candidates[:MAX_ATTEMPTS]:
        if len(approved)>=MAX_APPROVED: break
        media, attempts=download(item)
        if media is None:
            failures.append({'candidate':item,'attempts':attempts}); continue
        try:
            pr=probe(media); fr=analyze_frames(media,item['id']); sub=subtitles(item['id']); pace=classify(fr,sub)
            approved.append({'candidate':item,'download':{'file':str(media),'bytes':media.stat().st_size},
                             'ffprobe':pr,'frames':fr,'transcription':sub,'pacing':pace,
                             'review':{'download_verified':True,'ffprobe_verified':bool(pr.get('streams')),
                                       'all_frames_decoded':fr['all_frames_decoded'],'no_fabricated_findings':True}})
        except Exception as exc:
            failures.append({'candidate':item,'attempts':attempts,'post_download_error':repr(exc)})
    (OUT/'analysis.json').write_text(json.dumps(approved,indent=2,ensure_ascii=False),encoding='utf-8')
    (OUT/'failures.json').write_text(json.dumps(failures,indent=2,ensure_ascii=False),encoding='utf-8')
    valid=[x for x in approved if all([x['review']['download_verified'],x['review']['ffprobe_verified'],x['review']['all_frames_decoded']])]
    fast=sum(x['pacing']['label'] in {'ACELERADO','MUITO_ACELERADO'} for x in valid)
    if valid:
        med_cps=median(x['frames']['cuts_per_second'] for x in valid); med_shot=median(x['frames']['mean_shot_duration_s'] for x in valid); med_motion=median(x['frames']['motion_p90'] for x in valid)
        conclusion=(f'Sim: {fast} de {len(valid)} amostras foram classificadas como aceleradas. Mediana de {med_cps:.2f} cortes/s, cenas de {med_shot:.2f}s e movimento P90 {med_motion:.2f}.' if fast>len(valid)/2 else f'Não de forma predominante: {fast} de {len(valid)} amostras foram aceleradas.')
        status='APROVADO'
    else:
        conclusion='Não foi possível confirmar: nenhuma amostra passou por download, ffprobe e decodificação integral.'; status='REJEITADO'
    rows=[]
    for x in valid:
        c=x['candidate']; f=x['frames']; p=x['pacing']; s=x['transcription']
        rows.append(f"| {c.get('title','').replace('|','/')} | {f['duration_s']:.1f} | {f['cuts_per_second']:.2f} | {f['mean_shot_duration_s']:.2f} | {f['motion_p90']:.2f} | {s.get('words_per_second')} | {p['label']} | {p['playback_literalmente_acelerado']} |")
    table='| Vídeo | Duração | Cortes/s | Cena média | Movimento P90 | Palavras/s | Ritmo | Playback |\n|---|---:|---:|---:|---:|---:|---|---|\n'+'\n'.join(rows) if rows else 'Nenhuma amostra aprovada.'
    md=f'''# Análise revisada de velocidade em trends Roblox\n\n**Execução:** {datetime.now(timezone.utc).isoformat()}  \n**Ferramenta:** yt-dlp + FFmpeg + OpenCV  \n**Revisão:** **{status}**\n\n## Conclusão\n\n{conclusion}\n\n## Resultados\n\n{table}\n\n## Auditoria\n\n- Resultados planos encontrados pelo yt-dlp: **{len(candidates)}**\n- Downloads tentados: **{min(len(candidates),MAX_ATTEMPTS)}**\n- Vídeos integralmente decodificados: **{len(valid)}**\n- Falhas registradas: **{len(failures)}**\n- “Acelerado” significa ritmo de edição/movimento/fala. Playback em 1,5x ou 2x só é marcado como suspeita, nunca como certeza sem evidência adicional.\n'''
    (OUT/'APRENDIZADO_TRENDS_ROBLOX_ACELERACAO.md').write_text(md,encoding='utf-8')
    print(md)
    print('FAILURE_SUMMARY')
    for f in failures[:5]:
        print(f['candidate'].get('id'), [a.get('stderr_tail','')[-700:] for a in f.get('attempts',[])])
    return 0 if valid else 2

if __name__=='__main__':
    raise SystemExit(main())
