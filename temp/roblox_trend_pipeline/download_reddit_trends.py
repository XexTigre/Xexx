#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_reddit_trends'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_reddit_trend_download_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)

SUBREDDITS = ['roblox', 'bloxymemes', 'RobloxAvatars', 'robloxgamedev', 'RobloxDevelopers']
USER_AGENT = 'Mozilla/5.0 (compatible; RobloxTrendFrameResearch/1.0; +https://github.com/XexTigre/Xexx)'


def fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def extract_reddit_video(data):
    candidates = [data]
    candidates.extend(data.get('crosspost_parent_list') or [])
    for item in candidates:
        media = item.get('secure_media') or item.get('media') or {}
        video = media.get('reddit_video') or {}
        if video.get('dash_url') or video.get('fallback_url'):
            return video
    return None


def safe_slug(text, post_id):
    normalized = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:55]
    return f'{post_id}_{normalized or "roblox_video"}'


all_posts = {}
errors = []
for subreddit in SUBREDDITS:
    urls = [
        f'https://www.reddit.com/r/{subreddit}/top.json?t=month&limit=100&raw_json=1',
        f'https://www.reddit.com/r/{subreddit}/new.json?limit=100&raw_json=1',
    ]
    for url in urls:
        try:
            listing = fetch_json(url)
            for child in listing.get('data', {}).get('children', []):
                data = child.get('data', {})
                video = extract_reddit_video(data)
                if not video:
                    continue
                post_id = data.get('id')
                if not post_id:
                    continue
                created = float(data.get('created_utc') or 0)
                age_days = (time.time() - created) / 86400 if created else 9999
                if age_days > 60:
                    continue
                all_posts[post_id] = {
                    'post_id': post_id,
                    'title': data.get('title') or '',
                    'subreddit': data.get('subreddit') or subreddit,
                    'score': int(data.get('score') or 0),
                    'upvote_ratio': data.get('upvote_ratio'),
                    'num_comments': int(data.get('num_comments') or 0),
                    'created_utc': created,
                    'published_iso': datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else None,
                    'permalink': 'https://www.reddit.com' + (data.get('permalink') or ''),
                    'dash_url': video.get('dash_url'),
                    'fallback_url': video.get('fallback_url'),
                    'duration_s_reported': video.get('duration'),
                    'width_reported': video.get('width'),
                    'height_reported': video.get('height'),
                    'has_audio_reported': video.get('has_audio'),
                }
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})

ranked = sorted(
    all_posts.values(),
    key=lambda item: (item['score'], item['num_comments'], item['created_utc']),
    reverse=True,
)

# Diversify: prefer one post per subreddit before filling remaining slots.
selected = []
used_subreddits = set()
for post in ranked:
    if post['subreddit'].lower() not in used_subreddits:
        selected.append(post)
        used_subreddits.add(post['subreddit'].lower())
    if len(selected) == 3:
        break
for post in ranked:
    if len(selected) == 3:
        break
    if post['post_id'] not in {item['post_id'] for item in selected}:
        selected.append(post)

statuses = []
for post in selected:
    slug = safe_slug(post['title'], post['post_id'])
    output = VIDEO_DIR / f'{slug}.mp4'
    input_url = post.get('dash_url') or post.get('fallback_url')
    try:
        command = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
            '-user_agent', USER_AGENT, '-rw_timeout', '30000000', '-i', input_url,
            '-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-movflags', '+faststart', str(output),
        ]
        process = subprocess.run(command, capture_output=True, text=True, timeout=240)
        if process.returncode or not output.exists() or output.stat().st_size < 10000:
            raise RuntimeError((process.stderr or 'ffmpeg failed')[-6000:])
        post['slug'] = slug
        post['local_file'] = output.name
        post['downloaded_bytes'] = output.stat().st_size
        post['status'] = 'OK'
        statuses.append((slug, post['post_id'], 'OK', post['subreddit'], post['score'], output.stat().st_size))
    except Exception as exc:
        post['slug'] = slug
        post['status'] = 'FAILED'
        post['download_error'] = str(exc)
        statuses.append((slug, post['post_id'], 'FAILED', post['subreddit'], post['score'], 0))

(RESULT / 'reddit_candidates.json').write_text(json.dumps(ranked[:30], indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'selected_sources.json').write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'discovery_errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for row in statuses:
        file.write('\t'.join(map(str, row)) + '\n')

if not any(row[2] == 'OK' for row in statuses):
    sys.exit('No Reddit-hosted Roblox videos were downloaded')
