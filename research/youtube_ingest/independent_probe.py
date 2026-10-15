#!/usr/bin/env python3
"""Read-only, one-shot proof of independent YouTube public-source access.
No vidIQ, no API keys, no video files, no publication and no stock trading.
Never print or commit third-party transcripts; report access status only.
"""
from __future__ import annotations
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UCjNKuCKVBIQsrRdqJBWpkqA"  # 상상주식TV, user-supplied
TEST_VIDEO = "JSYuRdYKo2M"  # user-supplied public video
URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"


def status(kind: str, ok: bool, detail: str) -> dict[str, object]:
    return {"step": kind, "ok": ok, "detail": detail}


def channel_feed() -> dict[str, object]:
    try:
        req = urllib.request.Request(
            URL,
            headers={"User-Agent": "Mozilla/5.0 (independent-methodology-source-probe/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            document = response.read(400_000)
        root = ET.fromstring(document)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
        }
        videos = [
            (item.findtext("yt:videoId", default="", namespaces=ns),
             item.findtext("atom:title", default="", namespaces=ns))
            for item in root.findall("atom:entry", ns)
        ]
        return status("channel_public_feed", bool(videos), f"{len(videos)} video entries; first_id={videos[0][0] if videos else 'none'}")
    except Exception as exc:
        return status("channel_public_feed", False, f"{type(exc).__name__}: {str(exc)[:200]}")


def transcript_direct() -> dict[str, object]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi().fetch(TEST_VIDEO, languages=["ko"])
        snippets = transcript.snippets
        chars = sum(len(x.text) for x in snippets)
        return status("transcript_open_source", chars > 0, f"yt transcript: {len(snippets)} segments, {chars} characters (content NOT stored)")
    except Exception as exc:
        return status("transcript_open_source", False, f"{type(exc).__name__}: {str(exc)[:220]}")


def transcript_ytdlp() -> dict[str, object]:
    # Public subtitle metadata and retrieval only; never download video.
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = str(pathlib.Path(tmp) / "%(id)s.%(ext)s")
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--skip-download", "--write-subs", "--write-auto-subs",
                "--sub-langs", "ko", "--sub-format", "vtt",
                "--no-playlist", "--no-warnings",
                "--socket-timeout", "12", "--retries", "0",
                "--extractor-retries", "0", "--fragment-retries", "0",
                "-o", dest,
                f"https://www.youtube.com/watch?v={TEST_VIDEO}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=75, check=False)
            subtitles = list(pathlib.Path(tmp).glob("*.vtt"))
            bytes_n = sum(p.stat().st_size for p in subtitles)
            if result.returncode == 0 and bytes_n:
                return status("subtitles_open_source_fallback", True, f"yt-dlp: {len(subtitles)} vtt files, {bytes_n} bytes (content NOT stored)")
            # stderr often contains noisy and non-trustworthy tool messages; summarize
            error_lines = [ln for ln in result.stderr.splitlines() if "ERROR:" in ln]
            err = error_lines[-1][:180] if error_lines else f"exit={result.returncode}, no subtitle files"
            return status("subtitles_open_source_fallback", False, err)
    except Exception as exc:
        return status("subtitles_open_source_fallback", False, f"{type(exc).__name__}: {str(exc)[:180]}")


def main() -> None:
    findings = [channel_feed(), transcript_direct(), transcript_ytdlp()]
    result = {
        "probe": "USER_SUPPLIED_YOUTUBE_CHANNEL_NO_VIDIQ",
        "video_id": TEST_VIDEO,
        "feed_url": URL,
        "content_retained": False,
        "results": findings,
        "overall": "AT_LEAST_ONE_PATH_VERIFIED" if any(x["ok"] for x in findings) else "ALL_SOURCE_PATHS_UNVERIFIED",
        "claim_boundary": "Only source retrieval measured. Automatic visual chart comprehension and analytical improvement NOT TESTED.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    summ = os.getenv("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a", encoding="utf-8") as f:
            f.write("## Independent video-source probe (no vidIQ)\n")
            f.write(f"Source video: {TEST_VIDEO}. No transcript/video retained.\n")
            for x in findings:
                f.write(f"- {'PASS' if x['ok'] else 'BLOCKED'}: {x['step']} — {x['detail']}\n")
            f.write(f"\n**Result: {result['overall']}** (not a model-learning claim).\n")
    # This diagnostic produces unambiguous observations rather than hiding access
    # failures in "green" CI success. No production path depends on this status.
    if not any(x["ok"] for x in findings):
        sys.exit(2)


if __name__ == "__main__":
    main()
