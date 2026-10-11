"""Grok Video tools for AstrBot through Ace Data Cloud."""

from __future__ import annotations

import json

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .client import GrokVideoClient, GrokVideoError


class GrokVideoPlugin(Star):
    """Expose one video submission and one existing-task lookup tool."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @filter.llm_tool(name="grok_video_generate")
    async def grok_video_generate(
        self,
        event: AstrMessageEvent,
        prompt: str,
        model: str = "grok-imagine-video-1.5-fast:reverse",
        image_url: str = "",
        aspect_ratio: str = "16:9",
        resolution: str = "480p",
        duration: int = 6,
    ) -> str:
        """Submit one billable Grok Video text or image video job.

        Args:
            prompt(string): Description of the desired video.
            model(string): Supported Grok Imagine video model ID.
            image_url(string): Optional authorized HTTPS source image.
            aspect_ratio(string): Output ratio such as 16:9 or 9:16.
            resolution(string): 480p, 720p, or 1080p.
            duration(number): Model-supported video seconds.

        Returns:
            JSON submission status and task ID, never a finished-video claim.
        """
        try:
            result = await GrokVideoClient(self.config.get("api_key", "")).submit(
                prompt, model, image_url, aspect_ratio, resolution, duration
            )
        except GrokVideoError as exc:
            result = {"status": "error", "message": str(exc)}
        return json.dumps(result, ensure_ascii=False)

    @filter.llm_tool(name="grok_video_get_task")
    async def grok_video_get_task(self, event: AstrMessageEvent, task_id: str) -> str:
        """Query an existing Grok Video task without generating another video.

        Args:
            task_id(string): Exact task ID returned by grok_video_generate.

        Returns:
            JSON task status and final video URLs only after terminal success.
        """
        try:
            result = await GrokVideoClient(self.config.get("api_key", "")).query(
                task_id
            )
        except GrokVideoError as exc:
            result = {"status": "error", "message": str(exc), "task_id": task_id}
        return json.dumps(result, ensure_ascii=False)
