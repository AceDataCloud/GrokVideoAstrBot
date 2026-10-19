# Grok Video for AstrBot

Generate one Grok Imagine video in an AstrBot conversation through your own Ace Data Cloud account. `grok_video_generate` submits one text or image video job; `grok_video_get_task` queries the same task until its final video is ready.

This independent **Grok Video integration is provided by Ace Data Cloud**; it is not an official plugin from the Grok Video publisher or the AstrBot team. Use your own Ace API key.

[简体中文指南](readme/README_zh_Hans.md) · [Grok Videos API](https://platform.acedata.cloud/documents/grok-videos?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=grokvideoastrbot_readme_documents_grok_videos) · [Grok Tasks API](https://platform.acedata.cloud/documents/grok-tasks?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=grokvideoastrbot_readme_documents_grok_tasks) · [Current prices](https://platform.acedata.cloud/services/grok?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=grokvideoastrbot_readme_services_grok)

## 1. Find and install

Current upstream navigation is **Plugins → Plugins → Plugin Market / Installed**; older English versions may label the section Extensions. Search **Grok Video** and verify **Grok Video by Ace Data Cloud**, author **acedatacloud**, and the matching service icon.

**Publication status on 2026-10-19: not publicly listed in the official market.** The market search/install instructions above apply after publication. For the current preview, use the repository path below rather than waiting for a card that is not there.

Repository installation: **Plugins → Plugins → Installed → Install Plugin (+) → Install from URL**, with `https://github.com/AceDataCloud/GrokVideoAstrBot`. Source is already available. Confirm it is enabled and loaded. A repository/file installation is a separate path from official market installation.

## Configure your key

New account? Register and sign in first. If the Applications page has no General application yet, choose **Initialize General Application**, then continue with the key steps below.

In [Ace Data Cloud Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=grokvideoastrbot_readme_api_key), copy a generation API key from your General application or create a key that permits both `/grok/videos` and `/grok/tasks`. Check the current model, duration, and resolution price and your balance before submitting. Paste the key into the plugin's **Ace Data Cloud generation API key with Grok Video access** setting. Do not add `Bearer ` or use a `platform-...` management token. AstrBot masks the field in WebUI but stores the original value in its data directory, which should be protected.

Select a chat model that supports tool calling. Allow both Grok Video tools in the conversation's profile and persona.

### Token screenshots: copy or create a dedicated key

[Register or sign in to Ace](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=grokvideoastrbot_readme_signup), then open **Applications → General application** and initialize it if absent. Use **1** to copy the selected key, or **2 Manage Keys → Create** for a dedicated key. If Allowed APIs is enabled, include `/grok/tasks` and `/grok/videos`; check current entitlement, balance and prices before use.

![Copy an Ace key or open Manage Keys (redacted)](_assets/tutorial/get-api-key-en.png)

Use a name such as `AstrBot Grok Video` and set expiry/limits as needed. The screenshot’s `Dify tutorial` is an older example, not a required label.

![Create an optional dedicated API key (shared Ace page, not AstrBot)](_assets/tutorial/create-api-key-en.png)

Images were reused and checked on **2026-10-19**; original capture dates are unknown. Credentials, App ID and balance are redacted. This is the shared Ace Applications UI, not proof of AstrBot installation or a live service call. [Image sources and limits](_assets/tutorial/sources.json).

### Where to paste it in AstrBot

Open **Plugins → Plugins → Installed**, select the gear (**Plugin Configuration**) on **Grok Video by Ace Data Cloud**, paste the key into **Ace Data Cloud generation API key with Grok Video access** (stored field `api_key`), and save. Paste the key only, with no `Bearer ` prefix; never put it in model-provider settings or a chat prompt. UI masking does not encrypt the data-directory config. These are exact text steps; no fabricated settings image is used.

## Generate once, then query

Ask the bot:

> Use `grok_video_generate` exactly once to make a yellow paper kite rising over a calm green meadow. Use `grok-imagine-video-1.5-fast:reverse`, 6 seconds, 480p, 16:9. Show me the task ID.

The tool sends one asynchronous `POST /grok/videos` request and returns `status: submitted` with a task ID. Keep the ID and ask:

> Use `grok_video_get_task` with the exact task ID `<task_id>`. Tell me its status and final video URL. Do not generate another video.

If pending, query the same ID later. Only `status: succeeded`, `success: true`, and a final HTTPS video URL indicate completion. The plugin never retries a paid submission automatically.

The first version supports the four current public Grok Imagine video model names. The default fast model accepts 6–30 seconds; the other three accept 1–15 seconds. `grok-imagine-video-1.5:official` requires an image URL. To animate an image you own or may process, provide its public HTTPS `image_url`; other models also accept text alone. Supported resolutions are 480p, 720p, and 1080p. The model, duration, and resolution can change the price; some official model jobs may be charged even if moderation stops the output. Multiple reference images are outside this first version.

## Verify and troubleshoot

Match a returned trace ID in Ace Data Cloud usage when available. A finished task may include public `cost` amounts in Credits; confirm the live usage row before treating an estimate as a charge. Task lookup reads an existing job and does not submit another generation.

| Symptom | Check |
| --- | --- |
| Plugin fails to load | AstrBot version, **Failed to Load Plugins**, and **Data & Logs → Logs**. |
| Tools are missing | Plugin enabled, both tools allowed in the active profile and persona, chat model supports tool calling. |
| HTTP 401/403 | Key type, both allowed API paths, and account access. |
| Network error after submission | Inspect request history before generating again; a timeout may already have created a paid task. |
| Pending task | Query the same task ID later. |
| Failed task | Use the task or trace ID to inspect request history. |

The key goes only to `https://api.acedata.cloud`; redirects are rejected. The plugin exposes final video URLs and public cost fields to the model, without raw internal data. It uses Python's standard library and needs no runtime package installation.

## Validation and brand asset

On official AstrBot `v4.28.2`, an isolated editable installation registered both tools. ChatUI submitted one 6-second `grok-imagine-video-1.5-fast:reverse` text video at 480p and queried the same task ID twice; the first lookup was pending and the second returned success, with no second generation. The final MP4 responded HTTP 200, `video/mp4`, and decoded as H.264 video with AAC audio, 752×416, 6.042 seconds. The exact generation trace matched one successful `/grok/videos` usage row with 0.567 Credits deducted; the task returned 0.63 Credits as its list amount. See the [sanitized evidence](tests/e2e-results.json). Image-to-video and other models and settings were validated structurally but not generated. This is a local editable installation; official Cloud review, market installation, and a first call from a market installation remain open.

`logo.png` is the unmodified 400×400 [current Grok service icon](https://cdn.acedata.cloud/p1ge98.png), SHA-256 `8051b3d467ab852418f25c8057349313d4453b00b488b910ccdb5e233e44d7ab`.
