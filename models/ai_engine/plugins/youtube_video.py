import json
import re
import sys
import time
import subprocess
import platform
from pathlib import Path

import pyautogui
import numpy as np
import cv2
from PIL import ImageGrab

try:
    import requests
    from bs4 import BeautifulSoup
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _TRANSCRIPT_OK = True
except ImportError:
    _TRANSCRIPT_OK = False

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent / "Mark-XXXV"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def _get_api_key() -> str:
    sys.path.insert(0, str(get_base_dir()))
    from utils.api_keys import get_gemini_api_key
    return get_gemini_api_key()

def _extract_video_id(url: str) -> str | None:
    patterns = [r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([A-Za-z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def _is_valid_youtube_url(url: str) -> bool:
    return bool(re.search(r"(youtube\.com|youtu\.be)", url or ""))

def _get_transcript(video_id: str) -> str | None:
    if not _TRANSCRIPT_OK:
        return None
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en", "tr", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "ar", "zh"])
        except Exception:
            pass
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(["en", "tr", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "ar", "zh"])
            except Exception:
                for t in transcript_list:
                    transcript = t
                    break
        if transcript is None:
            return None
        fetched = transcript.fetch()
        return " ".join(entry["text"] for entry in fetched)
    except Exception:
        return None

def _summarize_with_gemini(transcript: str, video_url: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    max_chars = 80000
    truncated = transcript[:max_chars]
    response = model.generate_content(f"Summarize this YouTube video transcript:\n\n{truncated}")
    return response.text.strip()

def _scrape_video_info(video_id: str) -> dict:
    if not _REQUESTS_OK:
        return {}
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        html = r.text
        info = {}
        title_match = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"', html)
        if title_match:
            info["title"] = title_match.group(1)
        channel_match = re.search(r'"ownerChannelName":"([^"]+)"', html)
        if channel_match:
            info["channel"] = channel_match.group(1)
        views_match = re.search(r'"viewCount":"(\d+)"', html)
        if views_match:
            views = int(views_match.group(1))
            info["views"] = f"{views:,}"
        duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
        if duration_match:
            secs = int(duration_match.group(1))
            info["duration"] = f"{secs // 60}:{secs % 60:02d}"
        return info
    except Exception:
        return {}

def _scrape_trending(region: str = "TR", max_results: int = 8) -> list[dict]:
    if not _REQUESTS_OK:
        return []
    url = f"https://www.youtube.com/feed/trending?gl={region.upper()}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        html = r.text
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]', html)
        channels = re.findall(r'"ownerText":\{"runs":\[\{"text":"([^"]+)"', html)
        results = []
        seen = set()
        for i, title in enumerate(titles):
            if title in seen or len(title) < 5:
                continue
            seen.add(title)
            channel = channels[i] if i < len(channels) else "Unknown"
            results.append({"rank": len(results) + 1, "title": title, "channel": channel})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []

def _open_browser_and_play(query: str) -> str:
    try:
        from plugins.browser_control import open_url
        search_query = query.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={search_query}"
        open_url(url)
        return f"Opened YouTube search for: {query}"
    except Exception as e:
        return f"Failed to open YouTube: {e}"

def youtube_video(parameters: dict) -> str:
    params = parameters or {}
    action = params.get("action", "play").lower().strip()

    if action == "play":
        query = params.get("query", "").strip()
        if not query:
            return "Please specify what to watch."
        return _open_browser_and_play(query)

    elif action == "summarize":
        if not _TRANSCRIPT_OK:
            return "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"
        url = params.get("url", "").strip()
        if not url or not _is_valid_youtube_url(url):
            return "Please provide a valid YouTube URL."
        video_id = _extract_video_id(url)
        if not video_id:
            return "Could not extract video ID."
        transcript = _get_transcript(video_id)
        if not transcript:
            return "Could not retrieve transcript."
        return _summarize_with_gemini(transcript, url)

    elif action == "get_info":
        url = params.get("url", "").strip()
        if not url or not _is_valid_youtube_url(url):
            return "Please provide a valid YouTube URL."
        video_id = _extract_video_id(url)
        if not video_id:
            return "Could not extract video ID."
        info = _scrape_video_info(video_id)
        if not info:
            return "Could not retrieve video info."
        return "\n".join(f"{k.capitalize()}: {v}" for k, v in info.items())

    elif action == "trending":
        region = params.get("region", "TR").upper()
        trending = _scrape_trending(region=region, max_results=8)
        if not trending:
            return f"Could not fetch trending videos for {region}."
        lines = [f"Top trending videos in {region}:"]
        for item in trending:
            lines.append(f"{item['rank']}. {item['title']} — {item['channel']}")
        return "\n".join(lines)

    return f"Unknown action: '{action}'. Available: play, summarize, get_info, trending."
