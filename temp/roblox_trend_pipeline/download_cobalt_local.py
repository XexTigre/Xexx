#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_cobalt'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_cobalt_diagnostic_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)

API = os.environ.get('COBALT_API', 'http://127.0.0.1:9000/')
SOURCES = [
    ('pega_pega_aug02', 'ViAD2FfHsRc', 'https://www.youtube.com/shorts/ViAD2FfHsRc'),
    ('skyfall_aug01', 'A7sRDc3W6QQ', 'https://www.youtube.com/shorts/A7sRDc3W6QQ'),
    ('no_batidao_2026', 'znoKsfh8UDY', 'https://www.youtube.com/shorts/znoKsfh8UDY'),
]


def request_json(url, payload=None, timeout=90):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'RobloxTrendFrameResearch/1.0',
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def wait_for_api():
    errors = []
    for _ in range(40):
        try:
            return request_json(API, timeout=5)
        except Exception as exc:
            errors.append(str(exc))
            time.sleep(1)
    raise RuntimeError('Cobalt did not start: ' + ' | '.join(errors[-3:]))


def download_url(url, output):
    command = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
        '-rw_timeout', '60000000', '-i', url,
        '-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-movflags', '+faststart', str(output),
    ]
    process = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if process.returncode or not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError((process.stderr or 'ffmpeg failed')[-7000:])


def download_local_processing(response, output):
    tunnels = response.get('tunnel') or []
    if not tunnels:
        raise RuntimeError('local-processing without tunnels')
    command = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning']
    for tunnel in tunnels:
        command += ['-rw_timeout', '60000000', '-i', tunnel]
    if len(tunnels) >= 2:
        command += ['-map', '0:v:0', '-map', '1:a:0']
    else:
        command += ['-map', '0:v:0', '-map', '0:a?']
    command += ['-c', 'copy', '-movflags', '+faststart', str(output)]
    process = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if process.returncode or not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError((process.stderr or 'ffmpeg local processing failed')[-7000:])


instance_info = wait_for_api()
(RESULT / 'cobalt_instance.json').write_text(json.dumps(instance_info, indent=2), encoding='utf-8')
statuses = []
responses = []
errors = []
for slug, video_id, url in SOURCES:
    output = VIDEO_DIR / f'{slug}.mp4'
    try:
        response = request_json(API, {
            'url': url,
            'videoQuality': '720',
            'downloadMode': 'auto',
            'filenameStyle': 'basic',
            'youtubeVideoCodec': 'h264',
            'youtubeVideoContainer': 'mp4',
            'alwaysProxy': True,
            'localProcessing': 'preferred',
            'disableMetadata': True,
        })
        responses.append({'slug': slug, 'video_id': video_id, 'response': response})
        status = response.get('status')
        if status in ('tunnel', 'redirect'):
            download_url(response['url'], output)
        elif status == 'local-processing':
            download_local_processing(response, output)
        elif status == 'picker':
            videos = [item for item in response.get('picker', []) if item.get('type') == 'video' and item.get('url')]
            if not videos:
                raise RuntimeError('picker without video')
            download_url(videos[0]['url'], output)
        else:
            raise RuntimeError(json.dumps(response, ensure_ascii=False))
        statuses.append((slug, video_id, 'OK', status, output.stat().st_size))
    except Exception as exc:
        errors.append({'slug': slug, 'video_id': video_id, 'error': str(exc)})
        statuses.append((slug, video_id, 'FAILED', '', 0))

(RESULT / 'cobalt_responses.json').write_text(json.dumps(responses, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for row in statuses:
        file.write('\t'.join(map(str, row)) + '\n')
if not any(row[2] == 'OK' for row in statuses):
    sys.exit('Cobalt local did not download any video')
