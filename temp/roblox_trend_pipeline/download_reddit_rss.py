#!/usr/bin/env python3
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WORK = Path(os.environ.get('WORK_DIR', '/tmp/roblox_reddit_rss'))
RESULT = Path(os.environ.get('RESULT_DIR', 'temp/roblox_reddit_rss_diagnostic_2026-08-03'))
VIDEO_DIR = WORK / 'videos'
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULT.mkdir(parents=True, exist_ok=True)

SUBREDDITS = ['roblox', 'bloxymemes', 'RobloxAvatars', 'robloxgamedev', 'RobloxDevelopers']
USER_AGENT = 'Mozilla/5.0 (compatible; RobloxTrendFrameResearch/1.0)'


def fetch_text(url, timeout=25):
    request = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/atom+xml,application/rss+xml,text/html,*/*',
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='replace')


def find_vreddit_ids(text):
    text = html.unescape(text).replace('\\/', '/')
    return set(re.findall(r'https?://v\.redd\.it/([a-zA-Z0-9]+)', text))


def safe_slug(title, vid):
    name = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:55]
    return f'{vid}_{name or "roblox_video"}'


entries = []
errors = []
seen_links = set()
for subreddit in SUBREDDITS:
    feed_urls = [
        f'https://www.reddit.com/r/{subreddit}/top/.rss?t=month',
        f'https://www.reddit.com/r/{subreddit}/new/.rss',
        f'https://old.reddit.com/r/{subreddit}/top/.rss?t=month',
    ]
    for feed_url in feed_urls:
        try:
            xml_text = fetch_text(feed_url)
            root = ET.fromstring(xml_text)
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('a:entry', ns):
                title = entry.findtext('a:title', default='', namespaces=ns)
                link_node = entry.find('a:link', ns)
                link = link_node.get('href') if link_node is not None else ''
                content = entry.findtext('a:content', default='', namespaces=ns)
                updated = entry.findtext('a:updated', default='', namespaces=ns)
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                ids = find_vreddit_ids(content)
                page_text = ''
                if not ids:
                    page_variants = [
                        link.replace('www.reddit.com', 'old.reddit.com'),
                        link.replace('www.reddit.com', 'np.reddit.com'),
                        link,
                    ]
                    for page_url in page_variants:
                        try:
                            page_text = fetch_text(page_url)
                            ids = find_vreddit_ids(page_text)
                            if ids:
                                break
                        except Exception as exc:
                            errors.append({'url': page_url, 'error': str(exc)})
                for vreddit_id in ids:
                    entries.append({
                        'title': title,
                        'subreddit': subreddit,
                        'post_url': link,
                        'updated': updated,
                        'vreddit_id': vreddit_id,
                    })
        except Exception as exc:
            errors.append({'url': feed_url, 'error': str(exc)})

unique = {}
for entry in entries:
    unique[entry['vreddit_id']] = entry
entries = list(unique.values())[:12]
selected = entries[:3]
statuses = []
for entry in selected:
    vid = entry['vreddit_id']
    slug = safe_slug(entry['title'], vid)
    output = VIDEO_DIR / f'{slug}.mp4'
    manifest_urls = [
        f'https://v.redd.it/{vid}/DASHPlaylist.mpd',
        f'https://v.redd.it/{vid}/HLSPlaylist.m3u8',
    ]
    success = False
    for manifest in manifest_urls:
        try:
            command = [
                'ffmpeg', '-y', '-hide_banner', '-loglevel', 'warning',
                '-user_agent', USER_AGENT, '-rw_timeout', '30000000', '-i', manifest,
                '-map', '0:v:0', '-map', '0:a?', '-c', 'copy', '-movflags', '+faststart', str(output),
            ]
            process = subprocess.run(command, capture_output=True, text=True, timeout=240)
            if process.returncode or not output.exists() or output.stat().st_size < 10000:
                raise RuntimeError((process.stderr or 'ffmpeg failed')[-5000:])
            entry['slug'] = slug
            entry['manifest'] = manifest
            entry['downloaded_bytes'] = output.stat().st_size
            entry['status'] = 'OK'
            statuses.append((slug, vid, 'OK', entry['subreddit'], output.stat().st_size))
            success = True
            break
        except Exception as exc:
            errors.append({'url': manifest, 'error': str(exc)})
    if not success:
        entry['slug'] = slug
        entry['status'] = 'FAILED'
        statuses.append((slug, vid, 'FAILED', entry['subreddit'], 0))

(RESULT / 'rss_video_candidates.json').write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'selected_sources.json').write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
with (RESULT / 'download_status.tsv').open('w', encoding='utf-8') as file:
    for row in statuses:
        file.write('\t'.join(map(str, row)) + '\n')
if not any(row[2] == 'OK' for row in statuses):
    sys.exit('No Reddit RSS videos downloaded')
