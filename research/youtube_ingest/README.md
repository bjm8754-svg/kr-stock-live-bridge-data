# vidIQ-free public video source acquisition — current verified state

**Date:** 2026-10-15 (KST). **Target channel:** 상상주식TV `UCjNKuCKVBIQsrRdqJBWpkqA`. **Video:** `JSYuRdYKo2M`.

## What has actually been tried

- Read-only diagnostic script: `research/youtube_ingest/independent_probe.py`.
- One-time GitHub Actions run: https://github.com/bjm8754-svg/kr-stock-live-bridge-data/actions/runs/38664095258.
- Both tests used open-source libraries, **no vidIQ connection**, no API keys, no authenticated browser session, no commits of third-party transcripts or footage.
- **Verified GitHub-hosted results:** channel Atom feed `https://www.youtube.com/feeds/videos.xml?channel_id=UCjNKuCKVBIQsrRdqJBWpkqA` returned HTTP **404** on this runner; `youtube-transcript-api` returned **RequestBlocked**; `yt-dlp` returned **Sign in to confirm you are not a bot**. Therefore `ALL_SOURCE_PATHS_UNVERIFIED`. These results are specific to the tested cloud environment and video, not a claim that those tools never work anywhere.
- ChatGPT session sandbox network DNS also could not reach YouTube. Therefore **the vidIQ-free end-to-end ingestion and visual research pipeline has NOT been demonstrated in this environment**.

## Practical provider-independent routes, with unresolved prerequisites

1. **Local machine / self-hosted runner (preferred candidate to test next).** On a user-controlled Windows machine that is awake, try fetching captions via `youtube-transcript-api` or `yt-dlp` from its own network, then capture selective stills via FFmpeg when downloading the video is permitted. Scheduled Windows Task Scheduler and local Python can watch a channel and save a short *original analysis / structured excerpts with source IDs and timestamps* to the private GitHub study folder. No vidIQ is needed. **Do not assume a local IP is unblocked; run the independent probe locally first.** Avoid storing/re-publishing full copyrighted captions/footage unless rights permit. Never require the user to share cookies/passwords with ChatGPT or GitHub.
2. **Google YouTube Data API for public video discovery** (optional free Google Cloud API key / quotas; not a vidIQ app) can obtain channel/upload lists when the Atom feed is unavailable. **The official Captions Download endpoint requires edit permission on the video** and therefore does not solve caption retrieval for this third-party channel.
3. **Manual provision of source excerpts/files** is a fallback when automated lawful access remains blocked. The user's independent method can still study supplied snippets, but this is not unattended ingestion.
4. Paid hosted transcript services or residential proxy infrastructure are *other external dependencies*, not true app independence. **Do not silently switch to those or bill the user.**

## Suggested separate stages and truth conditions

1. Discovery (new video ID and publish time): `DISCOVERY_VERIFIED` only after real retrieval.
2. Captions/access: `TRANSCRIPT_ACQUIRED` only when actual original or auto captions are available and provenance is recorded. Summarized transcript text does **not** prove chart visuals were inspected.
3. Visual inspection: `VISUAL_VERIFIED` only after relevant price-chart frames are accessed; an automated screenshot is not proof of chart understanding.
4. Source-backed comparative analysis: read relevant 91 original numbered Library images, note host-vs-guest attribution, detect time-dependent claims and unverified trade returns. Hypotheses before rules.
5. GitHub update: only write when actual analysis was completed, with original observations, doubts and the next unknown; avoid duplicate video IDs and other experiments/scanner writes.

The existing ChatGPT scheduled research task **currently still uses a vidIQ-first approach**. The diagnostic above did not replace, disable or validate that automation. Do not say full independence exists until a source collector actually succeeds and it can feed the research loop.

## Repeat the independent probe on a Windows computer (optional future user-approved setup)

With Python 3.11+ and Internet access, in a clone of this repository:

```powershell
py -m pip install youtube-transcript-api yt-dlp
py research\youtube_ingest\independent_probe.py
```

The script prints only access statuses, segment/byte counts, and failures; it keeps no third-party transcript or footage. If at least one of its three paths succeeds, investigate the remaining stages **before** promising unattended study. A local collector, its scheduling and GitHub write access must be configured separately with user approval.

## Source documentation

- Original: https://github.com/jdepoix/youtube-transcript-api
- Original: https://github.com/yt-dlp/yt-dlp
- Official limitation: https://developers.google.com/youtube/v3/docs/captions/download

**No new scanner, S02 progression, actual brokerage trade, or production modification is authorized by this plan.**
