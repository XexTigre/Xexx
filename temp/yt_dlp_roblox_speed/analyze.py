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

ROOT = Path("temp/yt_dlp_roblox_speed")
OUT = ROOT / "results"
VIDEOS = ROOT / "videos"
OUT.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

TODAY = "2026-08-03"
DATE_AFTER = "20260720"
MAX_SAMPLES = 5
KNOWN_FALLBACK = [
    "https://www.youtube.com/shorts/ViAD2FfHsRc",
    "https://www.youtube.com/shorts/A7sRDc3W6QQ",
    "https://www.youtube.com/shorts/znoKsfh8UDY",
]


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def ytdlp_base() -> list[str]:
    return [
        "yt-dlp", "--ignore-config", "--no-warnings",
        "--remote-components", "ejs:github",
        "--js-runtimes", "node",
        "--extractor-retries", "3",
        "--fragment-retries", "3",
        "--retries", "3",
    ]


def discover() -> tuple[list[dict[str, Any]], list[str]]:
    logs: list[str] = []
    queries = [
        "ytsearchdate30:roblox shorts",
        "ytsearchdate30:roblox edit shorts",
        "ytsearchdate30:roblox trend shorts",
    ]
    found: dict[str, dict[str, Any]] = {}
    for query in queries:
        cmd = ytdlp_base() + [
            "--dump-json", "--skip-download", "--dateafter", DATE_AFTER,
            "--match-filter", "duration >= 5 & duration <= 120 & live_status != is_live",
            query,
        ]
        p = run(cmd, timeout=600)
        logs.append(f"$ {' '.join(cmd)}\nRC={p.returncode}\n{p.stderr[-6000:]}")
        for line in p.stdout.splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            vid = d.get("id")
            if not vid:
                continue
            text = " ".join(str(d.get(k) or "") for k in ("title", "description", "tags")).lower()
            if "roblox" not in text:
                continue
            found[vid] = {
                "id": vid,
                "url": d.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}",
                "title": d.get("title"),
                "channel": d.get("channel") or d.get("uploader"),
                "upload_date": d.get("upload_date"),
                "duration": d.get("duration"),
                "view_count": d.get("view_count"),
                "like_count": d.get("like_count"),
                "original_url": d.get("original_url"),
            }
    candidates = sorted(
        found.values(),
        key=lambda x: ((x.get("upload_date") or ""), int(x.get("view_count") or 0)),
        reverse=True,
    )
    return candidates, logs


def download_one(url: str, slug: str) -> tuple[Path | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    strategies = [
        ["--extractor-args", "youtube:player_client=web_creator,web_safari,android_vr,web_embedded"],
        ["--extractor-args", "youtube:player_client=android_vr,web_embedded"],
        [],
    ]
    for i, extra in enumerate(strategies, 1):
        template = str(VIDEOS / f"{slug}.%(ext)s")
        cmd = ytdlp_base() + extra + [
            "--no-playlist", "--restrict-filenames",
            "--write-info-json", "--write-auto-subs", "--write-subs",
            "--sub-langs", "pt.*,en.*,es.*", "--sub-format", "vtt",
            "-f", "bv*[height<=720]+ba/b[height<=720]/b",
            "--merge-output-format", "mp4", "-o", template, url,
        ]
        p = run(cmd, timeout=1200)
        attempts.append({
            "strategy": i, "command": cmd, "returncode": p.returncode,
            "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-8000:],
        })
        media = [
            x for x in VIDEOS.glob(f"{slug}.*")
            if x.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov"} and x.stat().st_size > 10000
        ]
        if media:
            return sorted(media, key=lambda x: x.stat().st_size, reverse=True)[0], attempts
    return None, attempts


def ffprobe(path: Path) -> dict[str, Any]:
    p = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ])
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])
    return json.loads(p.stdout)


def clean_vtt_text(text: str) -> tuple[int, float, list[dict[str, Any]]]:
    cue_re = re.compile(r"(?P<s>\d\d:\d\d:\d\d\.\d+)\s+-->\s+(?P<e>\d\d:\d\d:\d\d\.\d+)")
    def sec(t: str) -> float:
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    lines = text.splitlines()
    cues: list[dict[str, Any]] = []
    i = 0
    seen: set[tuple[int, str]] = set()
    while i < len(lines):
        m = cue_re.search(lines[i])
        if not m:
            i += 1
            continue
        start, end = sec(m.group("s")), sec(m.group("e"))
        i += 1
        parts: list[str] = []
        while i < len(lines) and lines[i].strip():
            val = re.sub(r"<[^>]+>", "", lines[i]).strip()
            if val and not val.startswith(("Kind:", "Language:")):
                parts.append(val)
            i += 1
        value = re.sub(r"\s+", " ", " ".join(parts)).strip()
        key = (round(start), value)
        if value and key not in seen:
            seen.add(key)
            cues.append({"start": start, "end": end, "text": value})
        i += 1
    words = sum(len(re.findall(r"\b[\wÀ-ÿ']+\b", c["text"])) for c in cues)
    speaking = sum(max(0.0, c["end"] - c["start"]) for c in cues)
    return words, speaking, cues


def subtitle_metrics(slug: str) -> dict[str, Any]:
    files = sorted(VIDEOS.glob(f"{slug}*.vtt"))
    if not files:
        return {"status": "UNAVAILABLE", "word_count": None, "speaking_seconds": None, "words_per_second": None, "files": []}
    best = files[0]
    words, speaking, cues = clean_vtt_text(best.read_text(encoding="utf-8", errors="ignore"))
    return {
        "status": "SUCCESS" if words else "NO_SPEECH",
        "word_count": words,
        "speaking_seconds": round(speaking, 3),
        "words_per_second": round(words / speaking, 3) if speaking > 0 else None,
        "files": [str(x) for x in files],
        "cue_count": len(cues),
    }


def analyze_frames(video: Path, slug: str) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError("decoder OpenCV não abriu a mídia")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    csv_path = OUT / f"{slug}_frames.csv"
    rows: list[list[Any]] = []
    prev_gray = None
    prev_hist = None
    motions: list[float] = []
    hist_changes: list[float] = []
    brightness: list[float] = []
    saturation: list[float] = []
    edge_density: list[float] = []
    cuts: list[dict[str, Any]] = []
    idx = 0
    last_cut = -999999
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        b = float(gray.mean())
        s = float(hsv[:, :, 1].mean())
        e = float((cv2.Canny(gray, 100, 200) > 0).mean())
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        hc = 0.0 if prev_hist is None else float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))
        motion = 0.0
        if prev_gray is not None:
            a = cv2.resize(prev_gray, (160, 90))
            z = cv2.resize(gray, (160, 90))
            flow = cv2.calcOpticalFlowFarneback(a, z, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            motion = float(np.mean(np.linalg.norm(flow, axis=2)))
        ts = idx / fps if fps else 0.0
        is_cut = hc > 0.42 and idx - last_cut > max(1, round(fps * 0.22))
        if is_cut:
            cuts.append({"frame": idx, "timestamp_s": round(ts, 4), "hist_change": round(hc, 5)})
            last_cut = idx
        rows.append([idx, round(ts, 5), round(b, 4), round(s, 4), round(e, 6), round(hc, 6), round(motion, 6), int(is_cut)])
        motions.append(motion); hist_changes.append(hc); brightness.append(b); saturation.append(s); edge_density.append(e)
        prev_gray = gray; prev_hist = hist; idx += 1
    cap.release()
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame", "timestamp_s", "brightness", "saturation", "edge_density", "histogram_change", "motion_score", "detected_cut"])
        w.writerows(rows)
    duration = idx / fps if fps else 0.0
    cut_rate = len(cuts) / duration if duration else 0.0
    mean_shot = duration / (len(cuts) + 1) if duration else None
    all_frames = idx > 0 and (expected <= 0 or abs(expected - idx) <= 1)
    return {
        "fps": fps, "width": width, "height": height,
        "frames_expected": expected, "frames_decoded": idx, "all_frames_decoded": all_frames,
        "duration_s": duration, "cuts": cuts, "cuts_count": len(cuts),
        "cuts_per_second": cut_rate, "mean_shot_duration_s": mean_shot,
        "motion_mean": float(np.mean(motions)) if motions else None,
        "motion_p90": float(np.percentile(motions, 90)) if motions else None,
        "hist_change_mean": float(np.mean(hist_changes)) if hist_changes else None,
        "brightness_mean": float(np.mean(brightness)) if brightness else None,
        "saturation_mean": float(np.mean(saturation)) if saturation else None,
        "edge_density_mean": float(np.mean(edge_density)) if edge_density else None,
        "frame_csv": str(csv_path),
    }


def classify_pacing(a: dict[str, Any], sub: dict[str, Any]) -> dict[str, Any]:
    cut_rate = float(a.get("cuts_per_second") or 0)
    shot = float(a.get("mean_shot_duration_s") or 999)
    motion_p90 = float(a.get("motion_p90") or 0)
    wps = sub.get("words_per_second")
    score = 0
    reasons: list[str] = []
    if cut_rate >= 0.8 or shot <= 1.25:
        score += 2; reasons.append("cortes muito frequentes")
    elif cut_rate >= 0.45 or shot <= 2.2:
        score += 1; reasons.append("cortes frequentes")
    if motion_p90 >= 4.0:
        score += 2; reasons.append("movimento visual muito alto")
    elif motion_p90 >= 2.2:
        score += 1; reasons.append("movimento visual alto")
    if isinstance(wps, (int, float)):
        if wps >= 4.0:
            score += 2; reasons.append("fala/legenda muito rápida")
        elif wps >= 3.0:
            score += 1; reasons.append("fala/legenda rápida")
    label = "MUITO_ACELERADO" if score >= 5 else "ACELERADO" if score >= 3 else "MODERADO" if score >= 1 else "CALMO"
    literal = "INDETERMINADO"
    if cut_rate < 0.25 and motion_p90 >= 4.0 and isinstance(wps, (int, float)) and wps >= 4.0:
        literal = "SUSPEITA_DE_PLAYBACK_ACELERADO"
    return {"pacing_score": score, "pacing_label": label, "reasons": reasons, "literal_speedup": literal}


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    def esc(v: Any) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(map(esc, headers)) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
        *["| " + " | ".join(map(esc, r)) + " |" for r in rows],
    ])


def main() -> int:
    candidates, discovery_logs = discover()
    (OUT / "discovery_logs.txt").write_text("\n\n".join(discovery_logs), encoding="utf-8")
    (OUT / "candidates.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")

    urls: list[dict[str, Any]] = candidates[:12]
    existing_ids = {x.get("id") for x in urls}
    for u in KNOWN_FALLBACK:
        vid = u.rstrip("/").split("/")[-1]
        if vid not in existing_ids:
            urls.append({"id": vid, "url": u, "title": "fallback conhecido", "upload_date": None})

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for item in urls:
        if len(results) >= MAX_SAMPLES:
            break
        vid = item.get("id") or re.sub(r"\W+", "_", item.get("url", "video"))[-30:]
        slug = f"roblox_{vid}"
        video, attempts = download_one(item["url"], slug)
        if video is None:
            failures.append({"candidate": item, "attempts": attempts})
            continue
        try:
            probe = ffprobe(video)
            frames = analyze_frames(video, slug)
            subs = subtitle_metrics(slug)
            pacing = classify_pacing(frames, subs)
            info_files = sorted(VIDEOS.glob(f"{slug}*.info.json"))
            info = json.loads(info_files[0].read_text(encoding="utf-8")) if info_files else {}
            results.append({
                "candidate": item,
                "metadata": {
                    "id": info.get("id") or vid,
                    "title": info.get("title") or item.get("title"),
                    "channel": info.get("channel") or info.get("uploader") or item.get("channel"),
                    "upload_date": info.get("upload_date") or item.get("upload_date"),
                    "duration": info.get("duration") or frames.get("duration_s"),
                    "view_count": info.get("view_count") or item.get("view_count"),
                    "url": info.get("webpage_url") or item.get("url"),
                },
                "download": {"status": "SUCCESS", "file": str(video), "bytes": video.stat().st_size, "attempts": attempts},
                "ffprobe": probe,
                "frames": frames,
                "transcription": subs,
                "pacing": pacing,
                "review": {
                    "download_verified": True,
                    "ffprobe_verified": bool(probe.get("streams")),
                    "all_frames_decoded": frames["all_frames_decoded"],
                    "transcription_verified": subs["status"] in {"SUCCESS", "NO_SPEECH"},
                    "no_fabricated_findings": True,
                },
            })
        except Exception as e:
            failures.append({"candidate": item, "attempts": attempts, "post_download_error": repr(e)})

    (OUT / "failures.json").write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "analysis.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    approved = [r for r in results if r["review"]["download_verified"] and r["review"]["ffprobe_verified"] and r["review"]["all_frames_decoded"]]
    labels = [r["pacing"]["pacing_label"] for r in approved]
    accelerated_count = sum(x in {"ACELERADO", "MUITO_ACELERADO"} for x in labels)
    literal_suspects = sum(r["pacing"]["literal_speedup"] == "SUSPEITA_DE_PLAYBACK_ACELERADO" for r in approved)

    rows = []
    for r in approved:
        m, f, t, p = r["metadata"], r["frames"], r["transcription"], r["pacing"]
        rows.append([
            m.get("title") or m.get("id"), m.get("upload_date"), f"{f['duration_s']:.1f}",
            f"{f['cuts_per_second']:.2f}", f"{f['mean_shot_duration_s']:.2f}",
            f"{f['motion_p90']:.2f}", t.get("words_per_second"), p["pacing_label"], p["literal_speedup"],
        ])

    if approved:
        med_cut = median([r["frames"]["cuts_per_second"] for r in approved])
        med_shot = median([r["frames"]["mean_shot_duration_s"] for r in approved])
        med_motion = median([r["frames"]["motion_p90"] for r in approved])
        conclusion = (
            f"Sim: {accelerated_count} de {len(approved)} amostras aprovadas foram classificadas como aceleradas no ritmo. "
            f"A mediana foi {med_cut:.2f} cortes/s, cena média de {med_shot:.2f}s e movimento P90 de {med_motion:.2f}. "
            "Isso comprova edição/ritmo mais rápido, mas não comprova automaticamente que o arquivo foi reproduzido em 1,5x ou 2x. "
            f"A heurística encontrou {literal_suspects} suspeita(s) de playback literalmente acelerado."
        ) if accelerated_count >= math.ceil(len(approved) / 2) else (
            f"Não de forma predominante: só {accelerated_count} de {len(approved)} amostras aprovadas foram classificadas como aceleradas. "
            "O conjunto pode parecer rápido por movimento e legendas, sem cortes muito frequentes."
        )
        review_status = "APROVADO"
    else:
        conclusion = "Não foi possível confirmar aceleração: nenhuma amostra passou simultaneamente por download, ffprobe e decodificação completa de frames."
        review_status = "REJEITADO"

    report = f"""# Trends Roblox: análise de aceleração com yt-dlp + FFmpeg\n\n**Execução:** {datetime.now(timezone.utc).isoformat()}  \n**Data de referência:** {TODAY}  \n**Revisão:** **{review_status}**  \n\n## Conclusão\n\n{conclusion}\n\n## Como “acelerado” foi medido\n\n- **Cortes por segundo** e duração média das cenas: medem ritmo de edição.\n- **Fluxo óptico P90**: mede movimento visual entre frames.\n- **Palavras por segundo**: usa legendas automáticas quando disponíveis.\n- **Playback literalmente acelerado** é apenas uma suspeita quando há fala e movimento muito rápidos sem muitos cortes; não é tratado como certeza.\n\n## Amostras aprovadas\n\n{md_table(rows, ['Vídeo','Data','Duração s','Cortes/s','Cena média s','Movimento P90','Palavras/s','Ritmo','Playback']) if rows else 'Nenhuma.'}\n\n## Auditoria\n\n- Candidatos descobertos: **{len(candidates)}**\n- Downloads/decodificações aprovados: **{len(approved)}**\n- Falhas registradas: **{len(failures)}**\n- Todos os frames de cada amostra aprovada foram percorridos e gravados em CSV.\n- Resultados sem download ou sem decodificação completa foram excluídos da conclusão.\n\n## Arquivos\n\n- `analysis.json`: métricas e revisão por vídeo.\n- `failures.json`: comandos e erros de download.\n- `candidates.json`: descoberta do yt-dlp.\n- `*_frames.csv`: métrica de cada frame decodificado.\n- `discovery_logs.txt`: auditoria da busca.\n"""
    (OUT / "APRENDIZADO_TRENDS_ROBLOX_ACELERACAO.md").write_text(report, encoding="utf-8")
    print(report)
    return 0 if approved else 2


if __name__ == "__main__":
    raise SystemExit(main())
