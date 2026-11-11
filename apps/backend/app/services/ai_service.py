import asyncio
import json
import logging
from typing import Any
from urllib import error, request

from app.ai.prompts import SYSTEM_PROMPT, user_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)


def _fallback(
    title: str,
    project_name: str | None = None,
    project_description: str | None = None,
) -> dict:
    clean = title.strip()
    project = (project_name or "this project").strip()
    context = (project_description or "").strip()
    context_bit = ""
    if context:
        first = context.split(".")[0].strip()
        if first:
            context_bit = f" Align with: {first}."

    description = (
        f"Goal: deliver “{clean}” for {project} at the scope the title implies — "
        f"no extra features beyond that.{context_bit}\n"
        "Steps:\n"
        "1. Read the project description and note what already exists for this work.\n"
        "2. Do only what the title asks, using the project’s stack and domain terms.\n"
        "3. Verify the change (imports, docs, or a quick smoke check) and list blockers if any.\n"
        "Done when: the titled work is in place and nothing already implemented was duplicated.\n"
        "Blockers: confirm current repo state before rewriting existing modules."
    )
    return {"title": clean, "description": description, "source": "fallback"}


class AIService:
    async def generate_task(
        self,
        title: str,
        *,
        project_name: str,
        project_description: str | None = None,
        member_names: list[str] | None = None,
        existing_tasks: list[dict[str, Any]] | None = None,
        priority: int | None = None,
        due_at: str | None = None,
        parent_task_title: str | None = None,
    ) -> dict:
        clean = title.strip()
        if not clean:
            raise ValueError("Title is required")
        if not project_name.strip():
            raise ValueError("Project context is required")
        if not settings.NVIDIA_API_KEY:
            logger.warning("NVIDIA_API_KEY missing; using local task description draft")
            return _fallback(clean, project_name, project_description)

        prompt = user_prompt(
            clean,
            project_name=project_name,
            project_description=project_description,
            member_names=member_names or [],
            existing_tasks=existing_tasks or [],
            priority=priority,
            due_at=due_at,
            parent_task_title=parent_task_title,
        )
        # Nemotron-class models fill reasoning_content first. Budget must cover that plus the answer.
        payload = {
            "model": settings.NVIDIA_MODEL,
            "temperature": 0.35,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT + " Keep internal reasoning short so the final answer fits.",
                },
                {"role": "user", "content": prompt},
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

        def _extract(message: dict[str, Any]) -> str:
            text = message.get("content")
            if isinstance(text, str) and text.strip():
                return text.strip()
            reasoning = message.get("reasoning_content")
            if isinstance(reasoning, str) and "Goal:" in reasoning:
                # Last "Goal:" block is usually the drafted answer inside the trace.
                chunk = reasoning.rsplit("Goal:", 1)[-1]
                return f"Goal:{chunk}".strip()
            return ""

        def _call() -> str:
            with request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = _extract(body["choices"][0]["message"])
            if text:
                return text
            raise ValueError(
                f"empty model content (finish_reason={body['choices'][0].get('finish_reason')})"
            )

        try:
            content = await asyncio.to_thread(_call)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            logger.warning("NVIDIA generate-task HTTP %s: %s", exc.code, detail)
            return _fallback(clean, project_name, project_description)
        except (error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError, ValueError) as exc:
            logger.warning("NVIDIA generate-task failed: %s", exc)
            return _fallback(clean, project_name, project_description)

        if not content:
            logger.warning("NVIDIA generate-task returned empty content")
            return _fallback(clean, project_name, project_description)

        # Strip accidental fences or a leading "Description:" label.
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("text"):
                content = content[4:].lstrip()
        if content.lower().startswith("description:"):
            content = content.split(":", 1)[1].strip()

        return {"title": clean, "description": content, "source": "nvidia"}


ai_service = AIService()
