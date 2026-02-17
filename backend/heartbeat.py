"""Heartbeat system — periodic background prompts that make the agent proactive."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from config import settings
from protocol import serialize, new_message_id, HeartbeatStart

logger = logging.getLogger(__name__)

DEFAULT_HEARTBEATS: list[dict[str, Any]] = [
    {
        "id": "time_awareness",
        "name": "Time Awareness",
        "prompt": (
            "Notice the current time. If the user hasn't spoken in a while, "
            "consider a gentle check-in. If it's getting late, mention it naturally. "
            "If there's nothing to say, stay silent."
        ),
        "interval_minutes": 30,
        "enabled": True,
    },
    {
        "id": "memory_reflection",
        "name": "Memory Reflection",
        "prompt": (
            "Review today's conversation. Are there unresolved threads, open questions, "
            "or action items the user mentioned but didn't follow up on? "
            "If so, bring one up naturally. If not, stay silent."
        ),
        "interval_minutes": 60,
        "enabled": True,
    },
    {
        "id": "proactive_search",
        "name": "Proactive Search",
        "prompt": (
            "Think about what the user has been working on today. "
            "Consider searching for something trending or newly published that's relevant "
            "to their interests. Only speak if you find something genuinely useful."
        ),
        "interval_minutes": 120,
        "enabled": True,
    },
    {
        "id": "mood_energy_check",
        "name": "Mood/Energy Check",
        "prompt": (
            "Based on the conversation tone and pace, consider checking in on "
            "how the user is doing. Be warm and natural, not clinical. "
            "If the conversation has been flowing fine, stay silent."
        ),
        "interval_minutes": 45,
        "enabled": True,
    },
]


def load_heartbeats() -> list[dict[str, Any]]:
    """Load heartbeat configs from file, or return defaults."""
    path = settings.heartbeats_path
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load heartbeats config: %s", e)
    return DEFAULT_HEARTBEATS.copy()


def save_heartbeats(heartbeats: list[dict[str, Any]]) -> None:
    """Save heartbeat configs to file."""
    path = settings.heartbeats_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(heartbeats, f, indent=2)


class HeartbeatScheduler:
    """Manages periodic heartbeat tasks for a WebSocket connection."""

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws
        self._tasks: list[asyncio.Task] = []
        self._paused = False
        self._running = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    async def start(self) -> None:
        """Start all enabled heartbeat loops."""
        self._running = True
        heartbeats = load_heartbeats()

        for hb in heartbeats:
            if hb.get("enabled", False):
                task = asyncio.create_task(
                    self._heartbeat_loop(hb),
                    name=f"heartbeat_{hb['id']}",
                )
                self._tasks.append(task)

        logger.info("Started %d heartbeat tasks.", len(self._tasks))

    async def stop(self) -> None:
        """Cancel all heartbeat tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("All heartbeat tasks stopped.")

    async def _heartbeat_loop(self, hb: dict[str, Any]) -> None:
        """Run a single heartbeat on its interval."""
        interval_seconds = hb.get("interval_minutes", 30) * 60
        name = hb.get("name", "Unknown")
        prompt = hb.get("prompt", "")

        # Wait one full interval before first heartbeat
        await asyncio.sleep(interval_seconds)

        while self._running:
            try:
                # Wait while paused (agent is actively responding)
                while self._paused:
                    await asyncio.sleep(1)

                logger.info("Heartbeat firing: %s", name)
                message_id = new_message_id()

                # Notify client that a heartbeat is being processed
                await self._ws.send_text(serialize(HeartbeatStart(
                    heartbeat_name=name,
                    message_id=message_id,
                )))

                # Import here to avoid circular dependency
                from ws_handler import process_agent_response

                await process_agent_response(
                    self._ws,
                    user_text="",
                    message_id=message_id,
                    is_heartbeat=True,
                    heartbeat_name=name,
                    heartbeat_prompt=prompt,
                )

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error("Heartbeat %s error: %s", name, e)

            await asyncio.sleep(interval_seconds)
