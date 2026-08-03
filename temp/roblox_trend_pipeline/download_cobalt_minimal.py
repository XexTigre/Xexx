#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_cobalt_min'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_cobalt_minimal_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)
API = os.environ.get('COBALT_API', 'http://127.0.0.1:9000/')
SOURCES = [
    ('pega_pega_aug02', 'ViAD2FfHsRc'),
    ('skyfall_aug01', 'A7sRDc3W6QQ'),
    ('no_batidao_2026', 'znoKsfh8UDY'),
]


def call(payload=None, timeout=120):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API, data=data, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {'raw_body': body}
        return exc.code, parsed


def wait_api():
    for _ in range(40):
        code, body = call(None, 5)
        if code == 200:
            return body
        time.sleep(1)
    raise RuntimeError('API not ready')


def download(response, output):
    status = response.get('status')
    if status in ('tunnel', 'redirect'):
        urls = [response['url']]
    elif status == 'local-processing':
        urls = response.get('tunnel') or []
    elif status == 'picker':
        urls = [item['url'] for item in response.get('picker', []) if item.get('type') == 'video' and item.get('url')][:1]
    else:
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    if not urls:
        raise RuntimeError('response without downloadable URL')
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning']
    for url in urls:
        cmd += ['-rw_timeout', '60000000', '-i', url]
    if len(urls) >= 2:
        cmd += ['-map', '0:v:0', '-map', '1:a:0']
    else:
        cmd += ['-map', '0:v:0', '-map', '0:a?']
    cmd += ['-c', 'copy', '-movflags', '+faststart', str(output)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode or not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError((p.stderr or 'ffmpeg failed')[-6000:])


info = wait_api()
(RESULT / 'instance.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
all_attempts = []
statuses = []
for slug, video_id in SOURCES:
    watch_url = f'https://www.youtube.com/watch?v={video_id}'
    payloads = [
        {'url': watch_url},
        {'url': watch_url, 'videoQuality': '720'},
        {'url': watch_url, 'videoQuality': '720', 'youtubeVideoContainer': 'mp4', 'youtubeVideoCodec': 'h264'},
        {'url': watch_url, 'videoQuality': '720', 'downloadMode': 'auto', 'localProcessing': 'disabled'},
    ]
    success = False
    for index, payload in enumerate(payloads, 1):
        code, response = call(payload)
        all_attempts.append({'slug': slug, 'attempt': index, 'http_code': code, 'payload': payload, 'response': response})
        if code == 200 and response.get('status') not in (None, 'error'):
            try:
                output = VIDEO_DIR / f'{slug}.mp4'
                download(response, output)
                statuses.append((slug, video_id, 'OK', response.get('status'), output.stat().st_size, index))
                success = True
                break
            except Exception as exc:
                all_attempts[-1]['download_error'] = str(exc)
    if not success:
        statuses.append((slug, video_id, 'FAILED', '', 0, 0))

(RESULT / 'attempts.json').write_text(json.dumps(all_attempts, indent=2, ensure_ascii=False), encoding='utf-8')
with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for row in statuses:
        file.write('\t'.join(map(str, row)) + '\n')
if not any(row[2] == 'OK' for row in statuses):
    sys.exit('No Cobalt payload succeeded')
