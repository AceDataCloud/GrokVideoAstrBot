"""Bounded Grok Video submission and existing-task lookup for AstrBot."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://api.acedata.cloud"
FAST_MODEL = "grok-imagine-video-1.5-fast:reverse"
MODELS = {
    FAST_MODEL,
    "grok-imagine-video:reverse",
    "grok-imagine-video:official",
    "grok-imagine-video-1.5:official",
}
RESOLUTIONS = {"480p", "720p", "1080p"}
RATIOS = {"1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"}
FAILED = {"failed", "error", "cancelled", "canceled", "rejected"}


class _NoRedirect(HTTPRedirectHandler):
    """Keep the configured API key on the fixed Ace Data Cloud host."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(_NoRedirect)


class GrokVideoError(RuntimeError):
    """An error safe to return to an AstrBot conversation."""


def _valid_https_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.netloc
        and not parsed.username
        and not parsed.password
    )


class GrokVideoClient:
    """Submit one video or query one existing task without paid retries."""

    def __init__(self, api_key: str) -> None:
        token = api_key.strip()
        if (
            not token
            or token.lower().startswith("bearer ")
            or token.startswith("platform-")
        ):
            raise GrokVideoError(
                "Set an Ace Data Cloud generation API key in plugin settings."
            )
        self._api_key = token

    def _post(self, path: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        request = Request(
            API_BASE + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloudAstrBot/0.1.0",
            },
            method="POST",
        )
        try:
            with OPENER.open(request, timeout=90) as response:
                body = json.load(response)
                header_trace = response.headers.get(
                    "x-trace-id", ""
                ) or response.headers.get("x-request-id", "")
        except HTTPError as exc:
            raise GrokVideoError(
                f"Ace Data Cloud returned HTTP {exc.code}. Check service access and request history."
            ) from None
        except (URLError, TimeoutError, OSError):
            raise GrokVideoError(
                "The API connection failed. Check request history before submitting another video."
            ) from None
        except (ValueError, UnicodeError):
            raise GrokVideoError(
                "The API returned invalid JSON. Check request history before retrying."
            ) from None
        if not isinstance(body, dict):
            raise GrokVideoError("The API returned an unexpected response format.")
        return body, str(body.get("trace_id") or header_trace)

    async def submit(
        self,
        prompt: str,
        model: str = FAST_MODEL,
        image_url: str = "",
        aspect_ratio: str = "16:9",
        resolution: str = "480p",
        duration: int = 6,
    ) -> dict[str, Any]:
        """Submit one asynchronous text or image video request."""
        prompt = prompt.strip()
        if not prompt or len(prompt) > 4000:
            raise GrokVideoError("Provide a video prompt of 1–4000 characters.")
        if model not in MODELS:
            raise GrokVideoError("Choose a supported Grok Video model ID.")
        if resolution not in RESOLUTIONS:
            raise GrokVideoError("Resolution must be 480p, 720p, or 1080p.")
        if aspect_ratio not in RATIOS:
            raise GrokVideoError("Choose a supported aspect ratio.")
        maximum = 30 if model == FAST_MODEL else 15
        minimum = 6 if model == FAST_MODEL else 1
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not minimum <= duration <= maximum
        ):
            raise GrokVideoError(
                f"Duration for this model must be {minimum}–{maximum} seconds."
            )
        if model == "grok-imagine-video-1.5:official" and not image_url:
            raise GrokVideoError("This model requires an authorized image URL.")
        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "duration": duration,
            "async": True,
        }
        if image_url:
            if not _valid_https_url(image_url):
                raise GrokVideoError("Provide an authorized HTTPS reference image URL.")
            payload["image_url"] = image_url
        body, trace_id = await asyncio.to_thread(self._post, "/grok/videos", payload)
        if body.get("success") is False or body.get("error"):
            raise GrokVideoError(
                "Video submission was rejected. Check request history before trying again."
            )
        task_id = body.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise GrokVideoError(
                "No task ID was returned. Check request history before submitting again."
            )
        return {
            "status": "submitted",
            "task_id": task_id,
            "trace_id": trace_id,
            "next_step": "Query this same task ID; do not submit another video while it is pending.",
        }

    async def query(self, task_id: str) -> dict[str, Any]:
        """Return final video URLs only after terminal task success."""
        task_id = task_id.strip()
        if not task_id or len(task_id) > 128:
            raise GrokVideoError("Pass the exact task ID from Grok Video submission.")
        body, trace_id = await asyncio.to_thread(
            self._post, "/grok/tasks", {"id": task_id, "action": "retrieve"}
        )
        if body.get("success") is False or body.get("error"):
            raise GrokVideoError("Task lookup failed. Check request history.")
        response = body.get("response")
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except ValueError:
                response = None
        if not isinstance(response, dict):
            response = {}
        trace_id = str(response.get("trace_id") or body.get("trace_id") or trace_id)
        data = response.get("data")
        items = data if isinstance(data, list) else []
        states = {
            str(item.get("state") or item.get("status") or "").lower()
            for item in items
            if isinstance(item, dict)
        }
        if response.get("success") is False or response.get("error") or states & FAILED:
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "failed",
                "success": False,
                "video_urls": [],
            }
        if not body.get("finished_at") or response.get("success") is not True:
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "pending",
                "success": False,
                "video_urls": [],
            }
        urls = [
            item["video_url"]
            for item in items
            if isinstance(item, dict)
            and str(item.get("state") or item.get("status") or "").lower()
            == "succeeded"
            and isinstance(item.get("video_url"), str)
            and _valid_https_url(item["video_url"])
        ]
        cost = response.get("cost")
        public_cost = (
            {
                key: cost[key]
                for key in ("amount", "list_amount", "currency")
                if key in cost
            }
            if isinstance(cost, dict)
            else {}
        )
        return {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "succeeded" if urls else "failed",
            "success": bool(urls),
            "video_urls": urls,
            "video_count": len(urls),
            "cost": public_cost,
        }
