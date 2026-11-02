SYSTEM_PROMPT = (
    "You write concise task descriptions for a project task manager. "
    "Reply with only the description text, no title line and no markdown fences."
)


def user_prompt(title: str) -> str:
    return (
        f"Write a short description for this task: {title.strip()}\n"
        "Include the expected outcome and 2-4 concrete steps."
    )
