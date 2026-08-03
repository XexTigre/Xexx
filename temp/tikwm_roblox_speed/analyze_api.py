#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
import analyze

API_URL = "https://www.tikwm.com/api/"


def download_via_api(sample: dict[str, Any]) -> tuple[Path | None, list[dict[str, Any]]]:
    vid = sample["id"]
    attempts: list[dict[str, Any]] = []
    headers = {
        "User-Agent": analyze.UA,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.tikwm.com",
        "Referer": "https://www.tikwm.com/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    payloads = [
        {"url": vid, "count": 12, "cursor": 0, "web": 1, "hd": 1},
        {"url": f"https://m.tiktok.com/v/{vid}.html", "count": 12, "cursor": 0, "web": 1, "hd": 1},
        {"url": f"https://www.tiktok.com/@placeholder/video/{vid}", "count": 12, "cursor": 0, "web": 1, "hd": 1},
    ]
    for payload in payloads:
        try:
            response = requests.post(API_URL, data=payload, headers=headers, timeout=90)
            record: dict[str, Any] = {
                "stage": "api",
                "payload_url": payload["url"],
                "status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "bytes": len(response.content),
            }
            attempts.append(record)
            if response.status_code != 200:
                record["body_tail"] = response.text[-1000:]
                continue
            data = response.json()
            record["api_code"] = data.get("code")
            record["api_msg"] = data.get("msg")
            video_data = data.get("data") or {}
            media_candidates = [
                ("hdplay", video_data.get("hdplay")),
                ("play", video_data.get("play")),
                ("wmplay", video_data.get("wmplay")),
            ]
            for label, media_url in media_candidates:
                if not media_url:
                    continue
                media_url = urljoin("https://www.tikwm.com", media_url)
                media_headers = {
                    "User-Agent": analyze.UA,
                    "Referer": "https://www.tikwm.com/",
                    "Accept": "video/avc,video/mp4,video/*;q=0.9,*/*;q=0.8",
                }
                media = requests.get(media_url, headers=media_headers, timeout=180, allow_redirects=True)
                media_record = {
                    "stage": "media",
                    "kind": label,
                    "status": media.status_code,
                    "content_type": media.headers.get("content-type"),
                    "bytes": len(media.content),
                    "final_host": requests.utils.urlparse(media.url).netloc,
                }
                attempts.append(media_record)
                content_type = (media.headers.get("content-type") or "").lower()
                if media.status_code == 200 and len(media.content) > 10000 and "html" not in content_type:
                    path = analyze.VIDEOS / f"{vid}.mp4"
                    path.write_bytes(media.content)
                    return path, attempts
        except Exception as exc:
            attempts.append({"stage": "exception", "payload_url": payload["url"], "error": str(exc)})
    return None, attempts


analyze.download = download_via_api
raise SystemExit(analyze.main())
