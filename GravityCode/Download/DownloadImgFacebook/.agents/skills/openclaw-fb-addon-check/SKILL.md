---
name: "openclaw-fb-addon-check"
description: "Use OpenClaw to diagnose Facebook media-downloader addon behavior on a user-authorized test tab, including Reel media classification and safe evidence collection."
---

# OpenClaw checks for the Facebook media downloader

Use this skill when a user asks to inspect or verify this project's Facebook addon with a live, user-authorized browser tab. It is for diagnosis and acceptance checks; do not use it to scan Activity Log or to change reactions unless the user explicitly asks to run the addon.

## Safe browser setup

- Confirm OpenClaw has a running Chrome profile and that the specific Facebook test tab appears in `openclaw browser tabs --browser-profile chrome`.
- With **Selected tabs** access, a newly opened tab is not automatically visible. Ask the user to select/allow that exact tab in the OpenClaw extension before diagnosing it.
- Use a dedicated Reel/post test tab. Do not navigate the Activity Log tab: preserving it is required for the addon's normal background-tab workflow.
- Begin with read-only commands: `browser status`, `browser tabs`, `browser snapshot`, and `browser evaluate`.
- When the addon-owned Background Runner is enabled, expect the authenticated Facebook tab to be in its dedicated minimized Chrome profile. Do not require a visible normal Chrome window, but do require a real (non-headless) browser tab before performing a live check.

## Reel verification

1. Snapshot the test tab and confirm it contains a `Video player`; record only the relevant caption, duration, resolution, and whether a post image is present.
2. Read video elements and loaded media resources. A Facebook Reel can have a blank `video.src` while playing via Media Source Extensions.
3. Treat DASH/CMAF evidence as non-downloadable by direct `chrome.downloads`: URL markers such as `dash`, `m3u8`, `byterange`, `byte_start`, or container atoms/brands `moof`, `sidx`, `dash`, `cmfc` mean an init/index/media fragment rather than a complete MP4.
4. Report the distinction clearly:
   - direct, complete MP4 verified → the addon may download it;
   - streaming fragments only → the addon must skip it to avoid corrupt files.

## Acceptance criteria for this addon

- A video-only Reel must queue no images.
- Never count a video as downloaded until the background worker returns success.
- A video-only Reel may unlike only after that successful download/mux result; a failed or skipped download must retain the Like.
- If Facebook rejects that Unlike action, verify that a later scan retries Unlike without downloading the confirmed video again.
- Never use network playback requests as a substitute for a complete video file.
- For a post whose text exceeds the configured threshold, the addon must neither download media nor unlike it.

## When direct MP4 is unavailable

Do not claim the Reel downloaded successfully. Explain that correct download needs an explicit streaming download-and-mux implementation, typically via a user-approved local helper such as FFmpeg. This is a non-trivial feature: state the files to change, risks (temporary space, expired URLs, audio/video synchronization), and a verification plan before implementing it.

## Record keeping

After each material live check or fix, append the test URL, observed media type, evidence, outcome, and remaining limitation to `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\ProjectLog.md`.
