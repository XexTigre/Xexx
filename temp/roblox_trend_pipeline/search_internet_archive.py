#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

RESULT = Path(os.environ.get('RESULT_DIR', 'temp/ia_roblox_search_2026-08-03'))
RESULT.mkdir(parents=True, exist_ok=True)

queries = [
    '(title:(roblox) OR description:(roblox) OR subject:(roblox)) AND mediatype:(movies) AND publicdate:[2026-07-01 TO 2026-08-03]',
    '(title:(roblox) OR description:(roblox) OR subject:(roblox)) AND mediatype:(movies) AND date:[2026-07-01 TO 2026-08-03]',
    '(title:(roblox) OR description:(roblox) OR subject:(roblox)) AND mediatype:(movies)',
]
headers = {'User-Agent': 'RobloxTrendFrameResearch/1.0'}
all_docs = {}
errors = []
for query in queries:
    params = urllib.parse.urlencode({
        'q': query,
        'fl[]': 'identifier,title,description,subject,creator,date,publicdate,downloads,week,month,year',
        'sort[]': 'publicdate desc',
        'rows': 100,
        'page': 1,
        'output': 'json',
    })
    url = 'https://archive.org/advancedsearch.php?' + params
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
        for doc in payload.get('response', {}).get('docs', []):
            identifier = doc.get('identifier')
            if identifier:
                all_docs[identifier] = doc
        if all_docs:
            break
    except Exception as exc:
        errors.append({'query': query, 'url': url, 'error': str(exc)})

ranked = sorted(
    all_docs.values(),
    key=lambda d: (str(d.get('publicdate') or d.get('date') or ''), int(d.get('downloads') or 0)),
    reverse=True,
)
(RESULT / 'candidates.json').write_text(json.dumps(ranked, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'errors.json').write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding='utf-8')
(RESULT / 'status.txt').write_text(f'candidate_count={len(ranked)}\n', encoding='utf-8')
