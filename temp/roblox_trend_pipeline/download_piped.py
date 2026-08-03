#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_trend_analysis_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)

INSTANCES = [
    'https://pipedapi.kavin.rocks',
    'https://pipedapi.tokhmi.xyz',
    'https://pipedapi.moomoo.me',
    'https://pipedapi.syncpundit.io',
    'https://api-piped.mha.fi',
    'https://piped-api.garudalinux.org',
    'https://pipedapi.rivo.lol',
]

SOURCES = [
    ('pega_pega_aug02', 'ViAD2FfHsRc', 'https://www.youtube.com/shorts/ViAD2FfHsRc'),
    ('skyfall_aug01', 'A7sRDc3W6QQ', 'https://www.youtube.com/shorts/A7sRDc3W6QQ'),
    ('no_batidao_2026', 'znoKsfh8UDY', 'https://www.youtube.com/shorts/znoKsfh8UDY'),
]


def get_json(url: str, timeout: int = 35):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/150 Safari/537.36',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def quality_num(stream):
    q = str(stream.get('quality') or stream.get('qualityLabel') or '')
    m = re.search(r'(\d+)', q)
    return int(m.group(1)) if m else 0


def choose_video(streams):
    usable = [s for s in streams if s.get('url') and quality_num(s) <= 720]
    if not usable:
        usable = [s for s in streams if s.get('url')]
    usable.sort(key=lambda s: (
        quality_num(s),
        int(s.get('fps') or 0),
        int(s.get('bitrate') or 0),
        1 if str(s.get('format') or '').lower() == 'mp4' else 0,
    ), reverse=True)
    return usable[0] if usable else None


def choose_audio(streams):
    usable = [s for s in streams if s.get('url')]
    usable.sort(key=lambda s: (
        int(s.get('bitrate') or 0),
        1 if str(s.get('format') or '').lower() in ('m4a', 'mp4') else 0,
    ), reverse=True)
    return usable[0] if usable else None


def ffmpeg_download(video, audio, output: Path):
    vurl = video['url']
    video_only = bool(video.get('videoOnly'))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning', '-rw_timeout', '30000000', '-i', vurl]
    if video_only and audio:
        cmd += ['-rw_timeout', '30000000', '-i', audio['url'], '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-movflags', '+faststart', str(output)]
    else:
        cmd += ['-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-movflags', '+faststart', str(output)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if p.returncode != 0 or not output.exists() or output.stat().st_size < 10_000:
        raise RuntimeError((p.stderr or 'ffmpeg download failed')[-4000:])


status_rows = []
error_log = []
for slug, video_id, source_url in SOURCES:
    success = False
    for base in INSTANCES:
        endpoint = f'{base}/streams/{video_id}'
        try:
            data = get_json(endpoint)
            if data.get('error'):
                raise RuntimeError(str(data['error']))
            video = choose_video(data.get('videoStreams') or [])
            audio = choose_audio(data.get('audioStreams') or [])
            if not video:
                raise RuntimeError('no usable video stream')
            out = VIDEO_DIR / f'{slug}.mp4'
            ffmpeg_download(video, audio, out)
            metadata = {
                'slug': slug,
                'video_id': video_id,
                'source_url': source_url,
                'piped_instance': base,
                'title': data.get('title'),
                'duration': data.get('duration'),
                'uploader': data.get('uploader'),
                'views': data.get('views'),
                'selected_video': {k: video.get(k) for k in ('format','quality','fps','codec','bitrate','videoOnly')},
                'selected_audio': ({k: audio.get(k) for k in ('format','quality','codec','bitrate')} if audio else None),
            }
            (RESULT / f'{slug}_source_metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            status_rows.append((slug, video_id, 'OK', base, out.stat().st_size))
            success = True
            break
        except Exception as exc:
            error_log.append({'slug': slug, 'video_id': video_id, 'instance': base, 'error': str(exc)})
            time.sleep(1)
    if not success:
        status_rows.append((slug, video_id, 'FAILED', '', 0))

with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as f:
    for row in status_rows:
        f.write('\t'.join(map(str, row)) + '\n')
(RESULT / 'download_errors.json').write_text(json.dumps(error_log, indent=2, ensure_ascii=False), encoding='utf-8')

if not any(row[2] == 'OK' for row in status_rows):
    sys.exit('All Piped downloads failed')
