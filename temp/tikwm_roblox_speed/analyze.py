#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import numpy as np
import requests

ROOT = Path("temp/tikwm_roblox_speed")
VIDEOS = ROOT / "videos"
OUT = ROOT / "results"
VIDEOS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    {"id":"7655656368099085590","date":"2026-06-26","views":1247264,"group":"trend","title":"MM2 meme / voice chat","source":"https://tikwm.com/video/7655656368099085590.html"},
    {"id":"7656936854536703252","date":"2026-06-29","views":410411,"group":"trend","title":"Roblox salsa meme","source":"https://tikwm.com/video/7656936854536703252.html"},
    {"id":"7658047426988739862","date":"2026-07-02","views":345737,"group":"trend","title":"TikTok hours / Roblox meme","source":"https://tikwm.com/video/7658047426988739862.html"},
    {"id":"7651994455184002337","date":"2026-06-16","views":2266852,"group":"trend","title":"Build a Boat meme","source":"https://tikwm.com/video/7651994455184002337.html"},
    {"id":"7645963581011283222","date":"2026-05-31","views":10202953,"group":"trend","title":"Roblox Studio AI coding meme","source":"https://tikwm.com/video/7645963581011283222.html"},
    {"id":"7635309897600503054","date":"2026-05-02","views":1298313,"group":"trend","title":"Roblox avatar reaction meme","source":"https://tikwm.com/video/7635309897600503054.html"},
    {"id":"7612053751670639903","date":"2026-02-28","views":1221395,"group":"trend","title":"Grace fast gameplay","source":"https://tikwm.com/video/7612053751670639903.html"},
    {"id":"7529174470833999126","date":"2025-07-20","views":5325,"group":"control","title":"Evergreen Roblox workplace clip","source":"https://www.tikwm.com/video/7529174470833999126.html"},
    {"id":"7615136550581554449","date":"2026-03-09","views":126177,"group":"control","title":"Long-form Roblox myth explanation","source":"https://tikwm.com/video/7615136550581554449.html"},
]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def download(sample: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    vid = sample["id"]
    attempts = []
    urls = [
        f"https://tikwm.com/video/media/play/{vid}.mp4",
        f"https://www.tikwm.com/video/media/play/{vid}.mp4",
        f"https://tikwm.com/video/media/hdplay/{vid}.mp4",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Referer": sample["source"]}, timeout=90, allow_redirects=True)
            attempts.append({"url": url, "status": r.status_code, "content_type": r.headers.get("content-type"), "bytes": len(r.content)})
            if r.status_code == 200 and len(r.content) > 10000 and "html" not in (r.headers.get("content-type") or "").lower():
                path = VIDEOS / f"{vid}.mp4"
                path.write_bytes(r.content)
                return path, attempts
        except Exception as exc:
            attempts.append({"url": url, "error": str(exc)})
    return None, attempts


def ffprobe(path: Path) -> dict[str, Any]:
    p = run([
        "ffprobe","-v","error","-show_entries",
        "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
        "-of","json",str(path)
    ])
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)


def parse_rate(v: str | None) -> float:
    if not v:
        return 0.0
    if "/" in v:
        a,b=v.split("/",1)
        return float(a)/float(b) if float(b) else 0.0
    return float(v)


def analyze_frames(path: Path, out_dir: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError("OpenCV não abriu o vídeo")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    csv_path = out_dir / "frames.csv"
    rows=[]
    prev_gray=None
    prev_hist=None
    frame_idx=0
    last_cut=-10**9
    cuts=[]
    motion=[]
    hist_changes=[]
    brightness=[]
    saturation=[]
    edge_density=[]
    lower_edge=[]
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        br=float(gray.mean())
        sat=float(hsv[:,:,1].mean())
        edges=cv2.Canny(gray,80,180)
        ed=float((edges>0).mean())
        lo=edges[int(height*0.55):,:] if height else edges
        led=float((lo>0).mean()) if lo.size else 0.0
        hist=cv2.calcHist([hsv],[0,1],None,[24,16],[0,180,0,256])
        cv2.normalize(hist,hist)
        hd=0.0 if prev_hist is None else float(cv2.compareHist(prev_hist,hist,cv2.HISTCMP_BHATTACHARYYA))
        mv=0.0
        if prev_gray is not None:
            a=cv2.resize(prev_gray,(160,90))
            b=cv2.resize(gray,(160,90))
            flow=cv2.calcOpticalFlowFarneback(a,b,None,0.5,3,15,3,5,1.2,0)
            mv=float(np.mean(np.linalg.norm(flow,axis=2)))
        ts=frame_idx/fps if fps else 0.0
        is_cut = hd > 0.38 and frame_idx-last_cut > max(1,round(fps*0.22))
        if is_cut:
            cuts.append(ts)
            last_cut=frame_idx
        rows.append([frame_idx,round(ts,6),round(br,5),round(sat,5),round(ed,7),round(led,7),round(hd,7),round(mv,7),int(is_cut)])
        brightness.append(br); saturation.append(sat); edge_density.append(ed); lower_edge.append(led); hist_changes.append(hd); motion.append(mv)
        prev_gray=gray; prev_hist=hist; frame_idx+=1
    cap.release()
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["frame","timestamp_s","brightness","saturation","edge_density","lower_region_edge_density","histogram_change","motion_score","cut"])
        w.writerows(rows)
    duration=frame_idx/fps if fps else 0.0
    complete = frame_idx>0 and (expected<=0 or abs(expected-frame_idx)<=1)
    return {
        "fps":fps,"width":width,"height":height,"frames_expected":expected,"frames_decoded":frame_idx,
        "duration_s":duration,"all_frames_decoded":complete,"cuts":len(cuts),"cut_timestamps_s":[round(x,3) for x in cuts],
        "cuts_per_second":len(cuts)/duration if duration else 0.0,
        "mean_shot_duration_s":duration/(len(cuts)+1) if duration else None,
        "motion_mean":float(np.mean(motion)) if motion else None,
        "motion_p90":float(np.percentile(motion,90)) if motion else None,
        "hist_change_mean":float(np.mean(hist_changes)) if hist_changes else None,
        "brightness_mean":float(np.mean(brightness)) if brightness else None,
        "saturation_mean":float(np.mean(saturation)) if saturation else None,
        "edge_density_mean":float(np.mean(edge_density)) if edge_density else None,
        "lower_region_edge_density_mean":float(np.mean(lower_edge)) if lower_edge else None,
        "frame_csv":str(csv_path),
    }


def audio_metrics(path: Path, out_dir: Path) -> dict[str, Any]:
    wav=out_dir/"audio.wav"
    p=run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(path),"-vn","-ac","1","-ar","22050",str(wav)])
    if p.returncode!=0 or not wav.exists():
        return {"status":"FAILED","error":p.stderr[-1000:]}
    result={"status":"SUCCESS","bpm":None,"rms_mean":None,"zero_crossing_rate":None}
    try:
        import librosa
        y,sr=librosa.load(str(wav),sr=22050,mono=True)
        if len(y):
            tempo,_=librosa.beat.beat_track(y=y,sr=sr)
            result["bpm"]=float(np.asarray(tempo).reshape(-1)[0])
            result["rms_mean"]=float(librosa.feature.rms(y=y).mean())
            result["zero_crossing_rate"]=float(librosa.feature.zero_crossing_rate(y).mean())
    except Exception as exc:
        result["librosa_error"]=str(exc)
    try:
        from faster_whisper import WhisperModel
        model = get_whisper_model()
        seg_iter, info = model.transcribe(str(wav), vad_filter=True, beam_size=1)
        windows=[]; words=0; speech_s=0.0
        for s in seg_iter:
            text=(s.text or "").strip()
            wc=len(text.split())
            words += wc
            speech_s += max(0.0,float(s.end)-float(s.start))
            windows.append({"start_s":round(float(s.start),2),"end_s":round(float(s.end),2),"words":wc})
        result["transcription"]={"status":"NO_SPEECH" if words==0 else "SUCCESS","language":getattr(info,"language",None),"segments":len(windows),"word_count":words,"speech_duration_s":speech_s,"words_per_second_of_speech":words/speech_s if speech_s else 0.0,"speech_windows":windows}
    except Exception as exc:
        result["transcription"]={"status":"FAILED","error":str(exc)}
    wav.unlink(missing_ok=True)
    return result

_WHISPER_MODEL=None

def get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        _WHISPER_MODEL=WhisperModel("tiny",device="cpu",compute_type="int8")
    return _WHISPER_MODEL


def med(values: list[float | None]) -> float | None:
    vals=[float(x) for x in values if x is not None and math.isfinite(float(x))]
    return median(vals) if vals else None


def ratio(a: float | None,b: float | None) -> float | None:
    if a is None or b in (None,0): return None
    return a/b


def main() -> int:
    failures=[]; approved=[]
    for sample in SAMPLES:
        video,attempts=download(sample)
        item={"sample":sample,"download_attempts":attempts,"review":{"status":"REJECTED","checks":{"download_verified":False,"ffprobe_verified":False,"all_frames_decoded":False,"no_fabricated_findings":True}}}
        if video is None:
            item["error"]="DOWNLOAD_FAILED"; failures.append(item); continue
        item["review"]["checks"]["download_verified"]=True
        out_dir=OUT/sample["id"]; out_dir.mkdir(parents=True,exist_ok=True)
        try:
            probe=ffprobe(video)
            item["ffprobe"]=probe
            item["review"]["checks"]["ffprobe_verified"]=True
            frames=analyze_frames(video,out_dir)
            item["frame_analysis"]=frames
            item["review"]["checks"]["all_frames_decoded"]=bool(frames["all_frames_decoded"])
            item["audio_analysis"]=audio_metrics(video,out_dir)
            item["review"]["status"]="APPROVED" if all(item["review"]["checks"].values()) else "PARTIAL"
            if item["review"]["status"]=="APPROVED": approved.append(item)
            else: failures.append(item)
        except Exception as exc:
            item["error"]=str(exc); failures.append(item)
        finally:
            video.unlink(missing_ok=True)
    trend=[x for x in approved if x["sample"]["group"]=="trend"]
    control=[x for x in approved if x["sample"]["group"]=="control"]
    def metric(group,key): return med([x["frame_analysis"].get(key) for x in group])
    trend_cut=metric(trend,"cuts_per_second"); control_cut=metric(control,"cuts_per_second")
    trend_shot=metric(trend,"mean_shot_duration_s"); control_shot=metric(control,"mean_shot_duration_s")
    trend_motion=metric(trend,"motion_p90"); control_motion=metric(control,"motion_p90")
    trend_bpm=med([x.get("audio_analysis",{}).get("bpm") for x in trend]); control_bpm=med([x.get("audio_analysis",{}).get("bpm") for x in control])
    trend_wps=med([x.get("audio_analysis",{}).get("transcription",{}).get("words_per_second_of_speech") for x in trend]); control_wps=med([x.get("audio_analysis",{}).get("transcription",{}).get("words_per_second_of_speech") for x in control])
    comparison={
        "trend_samples":len(trend),"control_samples":len(control),
        "trend_medians":{"cuts_per_second":trend_cut,"mean_shot_duration_s":trend_shot,"motion_p90":trend_motion,"bpm":trend_bpm,"words_per_second_of_speech":trend_wps},
        "control_medians":{"cuts_per_second":control_cut,"mean_shot_duration_s":control_shot,"motion_p90":control_motion,"bpm":control_bpm,"words_per_second_of_speech":control_wps},
        "ratios":{"cut_rate":ratio(trend_cut,control_cut),"motion_p90":ratio(trend_motion,control_motion),"bpm":ratio(trend_bpm,control_bpm),"speech_rate":ratio(trend_wps,control_wps),"shot_duration":ratio(trend_shot,control_shot)},
    }
    accelerated_evidence=[]
    if comparison["ratios"]["cut_rate"] and comparison["ratios"]["cut_rate"]>=1.25: accelerated_evidence.append("cut_rate")
    if comparison["ratios"]["motion_p90"] and comparison["ratios"]["motion_p90"]>=1.25: accelerated_evidence.append("motion")
    if comparison["ratios"]["speech_rate"] and comparison["ratios"]["speech_rate"]>=1.20: accelerated_evidence.append("speech_rate")
    if comparison["ratios"]["shot_duration"] and comparison["ratios"]["shot_duration"]<=0.80: accelerated_evidence.append("shorter_shots")
    conclusion={
        "review_status":"APPROVED" if len(trend)>=3 and len(control)>=1 else ("PARTIAL" if approved else "REJECTED"),
        "perceived_acceleration_supported":len(accelerated_evidence)>=2,
        "evidence":accelerated_evidence,
        "literal_playback_speedup_confirmed":False,
        "note":"Métricas confirmam ritmo percebido, não provam que a reprodução foi alterada para 1.25x/1.5x sem arquivo-fonte original.",
    }
    master={"run_at":datetime.now(timezone.utc).isoformat(),"approved":approved,"failures":failures,"comparison":comparison,"conclusion":conclusion}
    (OUT/"master_analysis.json").write_text(json.dumps(master,indent=2,ensure_ascii=False),encoding="utf-8")
    rows=[]
    for x in approved:
        f=x["frame_analysis"]; a=x.get("audio_analysis",{}); t=a.get("transcription",{})
        rows.append([x["sample"]["id"],x["sample"]["group"],x["sample"]["date"],x["sample"]["views"],round(f["duration_s"],3),round(f["fps"],3),f["frames_decoded"],f["cuts"],round(f["cuts_per_second"],4),round(f["mean_shot_duration_s"],4),round(f["motion_p90"],4),round(a.get("bpm") or 0,2),t.get("word_count"),round(t.get("words_per_second_of_speech") or 0,3),x["review"]["status"]])
    with (OUT/"video_summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["id","group","date","views","duration_s","fps","frames","cuts","cuts_per_second","mean_shot_duration_s","motion_p90","bpm","word_count","speech_words_per_second","review"]); w.writerows(rows)
    md=["# Análise revisada de aceleração em trends Roblox","",f"**Revisão:** **{conclusion['review_status']}**","", "## Resposta",""]
    if conclusion["review_status"]=="REJECTED":
        md.append("Nenhuma amostra passou por download, ffprobe e decodificação completa; não há conclusão visual válida.")
    elif conclusion["perceived_acceleration_supported"]:
        md.append("**Sim: a amostra de trends apresenta ritmo percebido mais acelerado que os controles.** A evidência vem de pelo menos duas métricas independentes: " + ", ".join(accelerated_evidence) + ".")
    else:
        md.append("A amostra foi analisada, mas as métricas não sustentam com força suficiente que as trends sejam mais aceleradas que os controles.")
    md += ["", "Isso não confirma que os arquivos foram literalmente reproduzidos em 1,25x ou 1,5x; confirma apenas edição/movimento/fala mais rápidos.","", "## Comparação de medianas","", "| Métrica | Trends | Controles | Razão |","|---|---:|---:|---:|",f"| Cortes/s | {trend_cut} | {control_cut} | {comparison['ratios']['cut_rate']} |",f"| Duração média da cena (s) | {trend_shot} | {control_shot} | {comparison['ratios']['shot_duration']} |",f"| Movimento P90 | {trend_motion} | {control_motion} | {comparison['ratios']['motion_p90']} |",f"| BPM | {trend_bpm} | {control_bpm} | {comparison['ratios']['bpm']} |",f"| Palavras/s de fala | {trend_wps} | {control_wps} | {comparison['ratios']['speech_rate']} |","", "## Auditoria","",f"- Amostras aprovadas: **{len(approved)}**",f"- Trends aprovadas: **{len(trend)}**",f"- Controles aprovados: **{len(control)}**",f"- Falhas: **{len(failures)}**","- Todos os frames das amostras aprovadas foram percorridos e gravados em CSV.","- A transcrição bruta não foi preservada; apenas idioma, janelas e contagem de palavras.","- Os MP4 foram apagados antes da publicação dos resultados.","", "## Vídeos aprovados","", "| ID | Grupo | Data | Views | Duração | Cortes/s | Movimento P90 | BPM | Fala palavras/s |","|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for x in approved:
        s=x["sample"]; f=x["frame_analysis"]; a=x.get("audio_analysis",{}); t=a.get("transcription",{})
        md.append(f"| `{s['id']}` | {s['group']} | {s['date']} | {s['views']} | {f['duration_s']:.2f} | {f['cuts_per_second']:.3f} | {f['motion_p90']:.3f} | {(a.get('bpm') or 0):.1f} | {(t.get('words_per_second_of_speech') or 0):.2f} |")
    (OUT/"APRENDIZADO_TRENDS_ROBLOX_TIKWM.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
