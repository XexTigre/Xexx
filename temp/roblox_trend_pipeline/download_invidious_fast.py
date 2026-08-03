#!/usr/bin/env python3
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_trend_analysis_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)

INSTANCES = [
    'https://inv.nadeko.net',
    'https://invidious.nerdvpn.de',
    'https://yt.chocolatemoo53.com',
    'https://invidious.tiekoetter.com',
]
SOURCES = [
    ('pega_pega_aug02', 'ViAD2FfHsRc', 'https://www.youtube.com/shorts/ViAD2FfHsRc'),
    ('skyfall_aug01', 'A7sRDc3W6QQ', 'https://www.youtube.com/shorts/A7sRDc3W6QQ'),
    ('no_batidao_2026', 'znoKsfh8UDY', 'https://www.youtube.com/shorts/znoKsfh8UDY'),
]


def fetch(base, video_id):
    endpoint = f'{base}/api/v1/videos/{video_id}?local=true'
    request = urllib.request.Request(endpoint, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/150 Safari/537.36',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.load(response)
        streams = data.get('formatStreams') or []
        if not streams:
            raise RuntimeError(data.get('error') or 'empty formatStreams')
        return {'ok': True, 'base': base, 'data': data}
    except Exception as exc:
        return {'ok': False, 'base': base, 'error': str(exc)}


def qnum(stream):
    match = re.search(r'(\d+)', str(stream.get('qualityLabel') or stream.get('quality') or ''))
    return int(match.group(1)) if match else 0


def pick_stream(items):
    items = [item for item in items if item.get('url')]
    bounded = [item for item in items if 0 < qnum(item) <= 720]
    if bounded:
        items = bounded
    return max(items, key=lambda item: (qnum(item), int(item.get('bitrate') or 0)), default=None)


def absolute_url(base, url):
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return base + url
    return url


def download(base, stream, output):
    url = absolute_url(base, stream['url'])
    command = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
        '-rw_timeout', '30000000', '-user_agent', 'Mozilla/5.0', '-i', url,
        '-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-movflags', '+faststart', str(output),
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if process.returncode or not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError((process.stderr or 'ffmpeg failed')[-5000:])


statuses = []
errors = []
for slug, video_id, source_url in SOURCES:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(INSTANCES)) as executor:
        futures = [executor.submit(fetch, base, video_id) for base in INSTANCES]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    successful = [response for response in responses if response['ok']]
    errors.extend({'slug': slug, 'video_id': video_id, 'instance': r['base'], 'error': r.get('error')} for r in responses if not r['ok'])
    downloaded = False
    for response in successful:
        data = response['data']
        stream = pick_stream(data.get('formatStreams') or [])
        if not stream:
            continue
        try:
            output = VIDEO_DIR / f'{slug}.mp4'
            download(response['base'], stream, output)
            metadata = {
                'slug': slug,
                'video_id': video_id,
                'source_url': source_url,
                'invidious_instance': response['base'],
                'title': data.get('title'),
                'lengthSeconds': data.get('lengthSeconds'),
                'author': data.get('author'),
                'viewCount': data.get('viewCount'),
                'selected_stream': {key: stream.get(key) for key in ('container','quality','qualityLabel','resolution','fps','bitrate','encoding')},
            }
            (RESULT / f'{slug}_source_metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            statuses.append((slug, video_id, 'OK', response['base'], output.stat().st_size))
            downloaded = True
            break
        except Exception as exc:
            errors.append({'slug': slug, 'video_id': video_id, 'instance': response['base'], 'error': str(exc)})
    if not downloaded:
        statuses.append((slug, video_id, 'FAILED', '', 0))

with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for row in statuses:
        file.write('\t'.join(map(str, row)) + '\n')
(RESULT / 'download_errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
if not any(row[2] == 'OK' for row in statuses):
    sys.exit('All Invidious downloads failed')
