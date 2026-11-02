import asyncio
import json
from urllib import error, request

from app.ai.prompts import SYSTEM_PROMPT, user_prompt
from app.core.config import settings


def _fallback(title: str) -> dict:
    clean = title.strip()
    return {
        "title": clean,
        "description": (
            f"Complete “{clean}”.\n"
            "Define the outcome, list the steps, and call out anything that blocks the work."
        ),
    }


class AIService:
    async def generate_task(self, title: str) -> dict:
        clean = title.strip()
        if not clean:
            raise ValueError("Title is required")
        if not settings.NVIDIA_API_KEY:
            return _fallback(clean)

        payload = {
            "model": settings.NVIDIA_MODEL,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(clean)},
            ],
        }
        req = request.Request(
            f"{settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        def _call() -> str:
            with request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()

        try:
            content = await asyncio.to_thread(_call)
        except (error.URLError, error.HTTPError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
            return _fallback(clean)

        if not content:
            return _fallback(clean)
        return {"title": clean, "description": content}


ai_service = AIService()
