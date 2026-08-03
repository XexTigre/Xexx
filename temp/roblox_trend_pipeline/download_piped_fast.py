#!/usr/bin/env python3
import concurrent.futures
import json
import os
import re
import subprocess
import sys
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


def fetch(base, video_id):
    endpoint = f'{base}/streams/{video_id}'
    req = urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.load(response)
        if data.get('error'):
            raise RuntimeError(str(data['error']))
        if not data.get('videoStreams'):
            raise RuntimeError('empty videoStreams')
        return {'ok': True, 'base': base, 'data': data}
    except Exception as exc:
        return {'ok': False, 'base': base, 'error': str(exc)}


def qnum(stream):
    match = re.search(r'(\d+)', str(stream.get('quality') or stream.get('qualityLabel') or ''))
    return int(match.group(1)) if match else 0


def pick_video(items):
    items = [x for x in items if x.get('url')]
    bounded = [x for x in items if 0 < qnum(x) <= 720]
    if bounded:
        items = bounded
    return max(items, key=lambda x: (qnum(x), int(x.get('fps') or 0), int(x.get('bitrate') or 0)), default=None)


def pick_audio(items):
    items = [x for x in items if x.get('url')]
    return max(items, key=lambda x: int(x.get('bitrate') or 0), default=None)


def download(video, audio, output):
    command = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning', '-rw_timeout', '20000000', '-i', video['url']]
    if video.get('videoOnly') and audio:
        command += ['-rw_timeout', '20000000', '-i', audio['url'], '-map', '0:v:0', '-map', '1:a:0']
    else:
        command += ['-map', '0:v:0', '-map', '0:a?']
    command += ['-c', 'copy', '-movflags', '+faststart', str(output)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=150)
    if process.returncode or not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError((process.stderr or 'ffmpeg failed')[-5000:])


statuses = []
errors = []
for slug, video_id, source_url in SOURCES:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(INSTANCES)) as executor:
        futures = [executor.submit(fetch, base, video_id) for base in INSTANCES]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    successes = [r for r in responses if r['ok']]
    errors.extend({'slug': slug, 'video_id': video_id, 'instance': r['base'], 'error': r.get('error')} for r in responses if not r['ok'])
    downloaded = False
    for response in successes:
        data = response['data']
        video = pick_video(data.get('videoStreams') or [])
        audio = pick_audio(data.get('audioStreams') or [])
        if not video:
            continue
        try:
            output = VIDEO_DIR / f'{slug}.mp4'
            download(video, audio, output)
            metadata = {
                'slug': slug, 'video_id': video_id, 'source_url': source_url,
                'piped_instance': response['base'], 'title': data.get('title'),
                'duration': data.get('duration'), 'uploader': data.get('uploader'), 'views': data.get('views'),
                'selected_video': {k: video.get(k) for k in ('format','quality','fps','codec','bitrate','videoOnly')},
                'selected_audio': ({k: audio.get(k) for k in ('format','quality','codec','bitrate')} if audio else None),
            }
            (RESULT / f'{slug}_source_metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            statuses.append((slug, video_id, 'OK', response['base'], output.stat().st_size))
            downloaded = True
            break
        except Exception as exc:
            errors.append({'slug': slug, 'video_id': video_id, 'instance': response['base'], 'error': str(exc)})
    if not downloaded:
        statuses.append((slug, video_id, 'FAILED', '', 0))

with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as f:
    for row in statuses:
        f.write('\t'.join(map(str, row)) + '\n')
(RESULT / 'download_errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
if not any(row[2] == 'OK' for row in statuses):
    sys.exit('All parallel Piped downloads failed')
