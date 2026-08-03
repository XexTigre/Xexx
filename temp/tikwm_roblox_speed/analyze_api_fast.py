#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import numpy as np
import requests
import analyze

analyze.SAMPLES = [
    s for s in analyze.SAMPLES
    if s["id"] in {
        "7655656368099085590",
        "7656936854536703252",
        "7651994455184002337",
        "7645963581011283222",
        "7635309897600503054",
        "7529174470833999126",
    }
]


def fast_download(sample: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    headers = {
        "User-Agent": analyze.UA,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.tikwm.com",
        "Referer": "https://www.tikwm.com/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    for source in [sample["id"], f"https://m.tiktok.com/v/{sample['id']}.html"]:
        try:
            r = requests.post(
                "https://www.tikwm.com/api/",
                data={"url": source, "count": 12, "cursor": 0, "web": 1, "hd": 1},
                headers=headers,
                timeout=20,
            )
            rec: dict[str, Any] = {"stage": "api", "source": source, "status": r.status_code, "bytes": len(r.content)}
            attempts.append(rec)
            if r.status_code != 200:
                rec["body_tail"] = r.text[-800:]
                continue
            payload = r.json()
            rec["code"] = payload.get("code")
            rec["msg"] = payload.get("msg")
            data = payload.get("data") or {}
            for key in ("play", "hdplay", "wmplay"):
                media_url = data.get(key)
                if not media_url:
                    continue
                media_url = urljoin("https://www.tikwm.com", media_url)
                mr = requests.get(
                    media_url,
                    headers={"User-Agent": analyze.UA, "Referer": "https://www.tikwm.com/"},
                    timeout=45,
                    allow_redirects=True,
                )
                mrec = {
                    "stage": "media", "kind": key, "status": mr.status_code,
                    "bytes": len(mr.content), "content_type": mr.headers.get("content-type"),
                    "host": urlparse(mr.url).netloc,
                }
                attempts.append(mrec)
                if mr.status_code == 200 and len(mr.content) > 10000 and "html" not in (mr.headers.get("content-type") or "").lower():
                    path = analyze.VIDEOS / f"{sample['id']}.mp4"
                    path.write_bytes(mr.content)
                    return path, attempts
        except Exception as exc:
            attempts.append({"stage": "exception", "source": source, "error": str(exc)})
    return None, attempts


def fast_audio(path: Path, out_dir: Path) -> dict[str, Any]:
    wav = out_dir / "audio.wav"
    p = analyze.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "22050", str(wav)], timeout=180)
    if p.returncode != 0 or not wav.exists():
        return {"status": "FAILED", "error": p.stderr[-1000:], "transcription": {"status": "NOT_ATTEMPTED"}}
    result: dict[str, Any] = {"status": "SUCCESS", "bpm": None, "rms_mean": None, "zero_crossing_rate": None, "transcription": {"status": "NOT_ATTEMPTED"}}
    try:
        import librosa
        y, sr = librosa.load(str(wav), sr=22050, mono=True)
        if len(y):
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            result["bpm"] = float(np.asarray(tempo).reshape(-1)[0])
            result["rms_mean"] = float(librosa.feature.rms(y=y).mean())
            result["zero_crossing_rate"] = float(librosa.feature.zero_crossing_rate(y).mean())
    except Exception as exc:
        result["error"] = str(exc)
    wav.unlink(missing_ok=True)
    return result


analyze.download = fast_download
analyze.audio_metrics = fast_audio
raise SystemExit(analyze.main())
