#!/usr/bin/env python3
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_ia_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_ia_analysis_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)
UA = 'RobloxTrendFrameResearch/1.0 (+https://github.com/XexTigre/Xexx)'

SEARCH_QUERY = '(title:(roblox) OR description:(roblox) OR subject:(roblox)) AND mediatype:(movies) AND publicdate:[2026-07-01 TO 2026-08-03]'
TREND_WORDS = {
    'fyp': 30, 'short': 25, 'shorts': 25, 'trend': 35, 'viral': 35,
    'dance': 28, 'edit': 18, 'meme': 22, 'drawing': 16, 'artist': 12,
    'challenge': 22, 'escape': 16, 'escapa': 16, 'animation': 14,
    'roblox': 10, 'gameplay': 6, 'funny': 14, 'skit': 18,
}
EXCLUDE_WORDS = {
    'nsfw', 'gooner', 'predator', 'allegation', 'sexual', 'groom', 'abuse',
    'exposed', 'documentary', 'livestream', 'podcast', 'full movie', 'compilation',
}


def request_json(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def search_items():
    params = urllib.parse.urlencode({
        'q': SEARCH_QUERY,
        'fl[]': 'identifier,title,description,subject,creator,date,publicdate,downloads',
        'sort[]': 'publicdate desc',
        'rows': 200,
        'page': 1,
        'output': 'json',
    })
    payload = request_json('https://archive.org/advancedsearch.php?' + params)
    return payload.get('response', {}).get('docs', [])


def parse_duration(value):
    if value is None:
        return None
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        pass
    parts = text.split(':')
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return None


def normalize_title(value):
    return re.sub(r'[^a-z0-9]+', ' ', (value or '').lower()).strip()


def best_file(metadata):
    options = []
    for file in metadata.get('files', []):
        name = file.get('name') or ''
        lower = name.lower()
        if not lower.endswith('.mp4'):
            continue
        if any(token in lower for token in ('_thumb', '__ia_thumb', 'sample', 'spectrogram')):
            continue
        try:
            size = int(file.get('size') or 0)
        except ValueError:
            size = 0
        if size < 100_000 or size > 250_000_000:
            continue
        duration = parse_duration(file.get('length'))
        fmt = str(file.get('format') or '')
        source = str(file.get('source') or '')
        score = 0
        if source == 'original': score += 10
        if 'h.264' in fmt.lower() or 'mpeg4' in fmt.lower(): score += 10
        if duration is not None:
            if duration <= 60: score += 80
            elif duration <= 120: score += 65
            elif duration <= 180: score += 45
            elif duration <= 300: score += 20
            elif duration > 600: score -= 100
        else:
            score -= 5
        score += min(20, size / 10_000_000)
        options.append((score, file, duration, size))
    return max(options, key=lambda row: row[0], default=None)


def inspect_doc(doc):
    identifier = doc.get('identifier')
    try:
        metadata = request_json(f'https://archive.org/metadata/{urllib.parse.quote(identifier)}', timeout=60)
        chosen = best_file(metadata)
        if not chosen:
            return {'identifier': identifier, 'status': 'NO_MP4'}
        file_score, file, duration, size = chosen
        text = ' '.join(str(doc.get(key) or '') for key in ('title','description','subject')).lower()
        if any(word in text for word in EXCLUDE_WORDS):
            return {'identifier': identifier, 'status': 'EXCLUDED_TOPIC'}
        score = float(file_score)
        for word, weight in TREND_WORDS.items():
            if word in text:
                score += weight
        publicdate = str(doc.get('publicdate') or '')
        if publicdate.startswith('2026-08-03'): score += 35
        elif publicdate.startswith('2026-08-02'): score += 30
        elif publicdate.startswith('2026-08-01'): score += 25
        elif publicdate.startswith('2026-07'): score += 10
        title_norm = normalize_title(doc.get('title'))
        return {
            'identifier': identifier,
            'status': 'CANDIDATE',
            'score': round(score, 3),
            'title': doc.get('title'),
            'title_normalized': title_norm,
            'creator': doc.get('creator'),
            'description': doc.get('description'),
            'subject': doc.get('subject'),
            'date': doc.get('date'),
            'publicdate': doc.get('publicdate'),
            'downloads': doc.get('downloads'),
            'file': {
                'name': file.get('name'),
                'format': file.get('format'),
                'source': file.get('source'),
                'size': size,
                'length_metadata_s': duration,
                'sha1': file.get('sha1'),
                'md5': file.get('md5'),
            },
        }
    except Exception as exc:
        return {'identifier': identifier, 'status': 'ERROR', 'error': str(exc)}


def download(candidate, destination):
    identifier = candidate['identifier']
    filename = candidate['file']['name']
    url = f'https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(filename)}'
    request = urllib.request.Request(url, headers={'User-Agent': UA})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=180) as response, destination.open('wb') as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            out.write(chunk)
    return url, digest.hexdigest(), destination.stat().st_size


def probe(path):
    proc = subprocess.run([
        'ffprobe','-v','error','-show_entries','format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels',
        '-of','json',str(path)
    ], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


docs = search_items()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    inspected = list(pool.map(inspect_doc, docs[:100]))
ranked = sorted(
    [item for item in inspected if item.get('status') == 'CANDIDATE'],
    key=lambda item: item.get('score', 0), reverse=True,
)

selected = []
seen_titles = set()
errors = []
for candidate in ranked:
    if len(selected) >= 3:
        break
    title_key = candidate.get('title_normalized') or candidate['identifier']
    title_key = re.sub(r'\b2026\d*\b', '', title_key).strip()
    if title_key in seen_titles:
        continue
    safe_slug = re.sub(r'[^a-z0-9]+', '_', (candidate.get('title') or candidate['identifier']).lower()).strip('_')[:55]
    safe_slug = f'{len(selected)+1:02d}_{safe_slug}'
    destination = VIDEO_DIR / f'{safe_slug}.mp4'
    try:
        url, sha256, downloaded_size = download(candidate, destination)
        media_probe = probe(destination)
        duration = float(media_probe.get('format', {}).get('duration') or 0)
        if duration <= 0 or duration > 360:
            destination.unlink(missing_ok=True)
            errors.append({'identifier': candidate['identifier'], 'reason': 'DURATION_REJECTED', 'duration_s': duration})
            continue
        candidate['slug'] = safe_slug
        candidate['download_url'] = url
        candidate['sha256_downloaded'] = sha256
        candidate['downloaded_size'] = downloaded_size
        candidate['ffprobe'] = media_probe
        candidate['duration_verified_s'] = duration
        candidate['status'] = 'DOWNLOADED'
        selected.append(candidate)
        seen_titles.add(title_key)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        errors.append({'identifier': candidate['identifier'], 'reason': 'DOWNLOAD_OR_PROBE_ERROR', 'error': str(exc)})

(RESULT / 'all_inspected_candidates.json').write_text(json.dumps(inspected, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'ranked_candidates.json').write_text(json.dumps(ranked[:30], indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'selected_sources.json').write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'selection_errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for item in selected:
        file.write(f"{item['slug']}\t{item['identifier']}\tOK\t{item['duration_verified_s']:.3f}\t{item['downloaded_size']}\n")
if len(selected) < 3:
    sys.exit(f'Only {len(selected)} suitable videos were downloaded')
