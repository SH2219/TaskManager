from typing import Any


SYSTEM_PROMPT = (
    "You write task descriptions for a software project team. "
    "Ground every word in the project description and the task title. "
    "Match the title’s real scope — a folder-structure or packaging task is layout/"
    "imports/smoke-check only, not schemas, models, CRUD, config, or deploy work. "
    "When the project already has a working backend, write steps that map, align, or "
    "verify existing packages — never “create backend/app or main.py from scratch.” "
    "Never open with “Complete …” and never use filler like "
    "“Define the outcome, list the steps, and call out anything that blocks the work.” "
    "Reply with plain text only — no title line, no markdown fences, no preamble."
)


def _line(label: str, value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f"{label}: {text}"


def _existing_backend_hints(project_description: str | None) -> list[str]:
    if not project_description:
        return []
    lower = project_description.lower()
    markers = (
        "current backend scope",
        "backend implements",
        "already",
        "working backend",
        "this repository currently contains",
    )
    if not any(marker in lower for marker in markers):
        return []
    return [
        "",
        "Important context flags",
        "- The project description indicates a backend already exists or is in progress.",
        "- Do not invent greenfield “create the app/folder tree from scratch” steps.",
        "- Prefer: map current packages → add only missing dirs → wire imports → verify Swagger/docs.",
        "- Do not add steps for new Pydantic schemas, SQLAlchemy models, or CRUD routers "
        "unless the title explicitly asks for them.",
    ]


def user_prompt(
    title: str,
    *,
    project_name: str,
    project_description: str | None = None,
    member_names: list[str] | None = None,
    existing_tasks: list[dict] | None = None,
    priority: int | None = None,
    due_at: str | None = None,
    parent_task_title: str | None = None,
) -> str:
    sections: list[str] = [
        "Write a practical description for this new task.",
        "",
        "Project",
    ]
    for item in (
        _line("Name", project_name),
        _line("Description", project_description or "No project description provided."),
        _line("Team", ", ".join(member_names) if member_names else "No members listed."),
    ):
        if item:
            sections.append(item)

    sections.extend(_existing_backend_hints(project_description))

    sections.extend(["", "Task to describe"])
    for item in (
        _line("Title", title.strip()),
        _line("Priority", priority),
        _line("Due date", due_at),
        _line("Parent task", parent_task_title),
    ):
        if item:
            sections.append(item)

    sections.extend(["", "Existing tasks in this project"])
    if existing_tasks:
        for task in existing_tasks[:20]:
            status = task.get("status") or "todo"
            task_title = task.get("title") or "Untitled"
            parent = task.get("parent_title")
            suffix = f" (subtask of {parent})" if parent else ""
            sections.append(f"- [{status}] {task_title}{suffix}")
    else:
        sections.append("- None yet")

    sections.extend(
        [
            "",
            "Write the description exactly in this shape:",
            "Goal: one sentence — what this title delivers in this project, without expanding scope.",
            "Steps: 2-4 numbered actions that fit only this title (use the project’s domain words).",
            "Done when: 1-2 short acceptance checks.",
            "Blockers: one short line if something must be confirmed first; otherwise omit this line.",
            "",
            "Rules:",
            "- Treat the project description as source of truth for stack, domains, and what already exists.",
            "- Keep the work as narrow as the title.",
            "- Use domain terms from the project (e.g. Category → ProductType → Product) when relevant.",
            "- Do not copy other task titles as steps.",
            "- Do not invent people, dates, repos, or tools that are not in the context.",
            "- Keep it under 140 words.",
            "",
            "Good Goal example for a structure task: "
            "“Lay out backend/app packages for the project domains without reworking features that already exist.”",
            "Bad Goal example: "
            "“Add Pydantic schemas, SQLAlchemy models, and CRUD routers for every entity from scratch.”",
            "Good Steps example for a structure task: "
            "1) Map current backend/app folders to the domain modules. "
            "2) Add only missing package dirs with __init__.py. "
            "3) Wire missing imports in main.py. "
            "4) Run the documented start command and confirm docs/Swagger still load.",
            "Bad Steps example: "
            "Create models and CRUD for Product, Category, Store, Vendor, Bill from scratch.",
        ]
    )
    return "\n".join(sections)
