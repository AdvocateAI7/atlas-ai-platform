from pathlib import Path

from app.core.config import get_settings


def log_prompt(source: str, prompt: str) -> None:
    settings = get_settings()
    path = Path(settings.prompt_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{source}\t{prompt}\n")
